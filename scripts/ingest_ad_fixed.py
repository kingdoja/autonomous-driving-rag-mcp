#!/usr/bin/env python
"""
自动驾驶文档摄取脚本 - 修复版

这个脚本在文档加载后立即添加 document_type 元数据标签。

Usage:
    python scripts/ingest_ad_fixed.py --path demo-data-ad --collection ad_knowledge_v01
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Ensure project root is on sys.path
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_REPO_ROOT))

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.core.settings import load_settings
from src.core.trace import TraceContext, TraceCollector
from src.ingestion.pipeline import IngestionPipeline, PipelineResult
from src.ingestion.metadata.ad_metadata_tagger import ADMetadataTagger
from src.observability.logger import get_logger

logger = get_logger(__name__)


def discover_files(path: str, extensions: List[str] = None) -> List[Path]:
    """Discover files to process from path."""
    if extensions is None:
        extensions = ['.pdf', '.txt']
    
    path = Path(path)
    
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    if path.is_file():
        if path.suffix.lower() in extensions:
            return [path]
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}. Supported: {extensions}")
    
    # Directory: recursively find all matching files
    files = []
    for ext in extensions:
        files.extend(path.rglob(f"*{ext}"))
        files.extend(path.rglob(f"*{ext.upper()}"))
    
    # Remove duplicates and sort
    files = sorted(set(files))
    
    return files


# Monkey-patch the IngestionPipeline.run method to add metadata
_original_run = IngestionPipeline.run

def patched_run(self, file_path: str, trace: Optional[TraceContext] = None, on_progress=None):
    """Patched run method that adds document_type metadata."""
    # Get metadata from ADMetadataTagger
    tagger = ADMetadataTagger()
    ad_metadata = tagger.tag_document(file_path)
    
    # Store metadata for later use
    self._ad_metadata = ad_metadata.to_dict() if ad_metadata else {}
    
    # Call original run method
    return _original_run(self, file_path, trace, on_progress)

# Apply the patch
IngestionPipeline.run = patched_run


# Also patch the loader to inject metadata
from src.libs.loader.pdf_loader import PdfLoader
from src.libs.loader.text_loader import TextLoader

_original_pdf_load = PdfLoader.load
_original_text_load = TextLoader.load

def patched_pdf_load(self, file_path):
    """Patched PDF load method that adds document_type metadata."""
    doc = _original_pdf_load(self, file_path)
    
    # Get pipeline instance from call stack to access _ad_metadata
    import inspect
    for frame_info in inspect.stack():
        frame_locals = frame_info.frame.f_locals
        if 'self' in frame_locals and isinstance(frame_locals['self'], IngestionPipeline):
            pipeline = frame_locals['self']
            if hasattr(pipeline, '_ad_metadata'):
                doc.metadata.update(pipeline._ad_metadata)
                logger.info(f"Added metadata to document: {pipeline._ad_metadata}")
            break
    
    return doc

def patched_text_load(self, file_path):
    """Patched text load method that adds document_type metadata."""
    doc = _original_text_load(self, file_path)
    
    # Get pipeline instance from call stack to access _ad_metadata
    import inspect
    for frame_info in inspect.stack():
        frame_locals = frame_info.frame.f_locals
        if 'self' in frame_locals and isinstance(frame_locals['self'], IngestionPipeline):
            pipeline = frame_locals['self']
            if hasattr(pipeline, '_ad_metadata'):
                doc.metadata.update(pipeline._ad_metadata)
                logger.info(f"Added metadata to document: {pipeline._ad_metadata}")
            break
    
    return doc

# Apply the patches
PdfLoader.load = patched_pdf_load
TextLoader.load = patched_text_load


def main():
    parser = argparse.ArgumentParser(
        description="自动驾驶文档摄取脚本 - 修复版"
    )
    
    parser.add_argument(
        "--path", "-p",
        required=True,
        help="文档路径（文件或目录）"
    )
    
    parser.add_argument(
        "--collection", "-c",
        default="ad_knowledge_v01",
        help="Collection 名称 (默认: ad_knowledge_v01)"
    )
    
    parser.add_argument(
        "--config",
        default="config/settings.ad_knowledge.yaml",
        help="配置文件路径 (默认: config/settings.ad_knowledge.yaml)"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制重新处理所有文档"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="试运行模式（不实际摄取）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("[*] 自动驾驶文档摄取脚本 - 修复版")
    print("=" * 60)
    
    # Load configuration
    try:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"[FAIL] 配置文件不存在: {config_path}")
            return 2
        
        settings = load_settings(str(config_path))
        print(f"[OK] 配置已加载: {config_path}")
    except Exception as e:
        print(f"[FAIL] 加载配置失败: {e}")
        return 2
    
    # Discover files
    try:
        files = discover_files(args.path)
        print(f"[INFO] 发现 {len(files)} 个文件")
        
        if len(files) == 0:
            print("[WARN] 没有找到文件")
            return 0
        
        if args.verbose:
            for f in files:
                print(f"   - {f}")
    except FileNotFoundError as e:
        print(f"[FAIL] {e}")
        return 2
    except ValueError as e:
        print(f"[FAIL] {e}")
        return 2
    
    # Dry run mode
    if args.dry_run:
        print("\n[INFO] 试运行模式 - 显示标签预览")
        print("=" * 60)
        
        tagger = ADMetadataTagger()
        for file_path in files:
            metadata = tagger.tag_document(str(file_path))
            if metadata:
                print(f"\n📄 {file_path.name}")
                print(f"   类型: {metadata.document_type}")
                if metadata.sensor_type:
                    print(f"   传感器类型: {metadata.sensor_type}")
                if metadata.algorithm_type:
                    print(f"   算法类型: {metadata.algorithm_type}")
                if metadata.regulation_type:
                    print(f"   法规类型: {metadata.regulation_type}")
                if metadata.test_type:
                    print(f"   测试类型: {metadata.test_type}")
            else:
                print(f"\n⚠️  {file_path.name} - 无法识别类型")
        
        print("\n" + "=" * 60)
        print(f"总计: {len(files)} 个文件")
        print("=" * 60)
        return 0
    
    # Initialize pipeline
    print(f"\n[INFO] 初始化流水线...")
    print(f"   Collection: {args.collection}")
    print(f"   强制重新处理: {args.force}")
    
    try:
        pipeline = IngestionPipeline(
            settings=settings,
            collection=args.collection,
            force=args.force
        )
    except Exception as e:
        print(f"[FAIL] 初始化流水线失败: {e}")
        logger.exception("Pipeline initialization failed")
        return 2
    
    # Process files
    print(f"\n[INFO] 处理文件...")
    results: List[PipelineResult] = []
    collector = TraceCollector()
    
    for i, file_path in enumerate(files, 1):
        print(f"\n[{i}/{len(files)}] 处理: {file_path.name}")
        
        try:
            trace = TraceContext(trace_type="ingestion")
            trace.metadata["source_path"] = str(file_path)
            result = pipeline.run(str(file_path), trace=trace)
            collector.collect(trace)
            results.append(result)
            
            if result.success:
                skipped = result.stages.get("integrity", {}).get("skipped", False)
                if skipped:
                    print(f"   [SKIP] 跳过（已处理）")
                else:
                    print(f"   [OK] 成功: {result.chunk_count} chunks, {result.image_count} images")
            else:
                print(f"   [FAIL] 失败: {result.error}")
        
        except Exception as e:
            logger.exception(f"处理文件时出错: {file_path}")
            results.append(PipelineResult(
                success=False,
                file_path=str(file_path),
                error=str(e)
            ))
            print(f"   [FAIL] 错误: {e}")
    
    # Print summary
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    total_chunks = sum(r.chunk_count for r in results if r.success)
    total_images = sum(r.image_count for r in results if r.success)
    
    print("\n" + "=" * 60)
    print("摄取摘要")
    print("=" * 60)
    print(f"总文件数: {total}")
    print(f"  ✅ 成功: {successful}")
    print(f"  ❌ 失败: {failed}")
    print(f"\n总 chunks: {total_chunks}")
    print(f"总 images: {total_images}")
    print("=" * 60)
    
    # Document type statistics
    tagger = ADMetadataTagger()
    doc_type_stats = {}
    for file_path in files:
        metadata = tagger.tag_document(str(file_path))
        if metadata:
            doc_type = metadata.document_type
            doc_type_stats[doc_type] = doc_type_stats.get(doc_type, 0) + 1
    
    if doc_type_stats:
        print(f"\n文档类型统计:")
        for doc_type, count in sorted(doc_type_stats.items()):
            print(f"  {doc_type}: {count}")
        print("=" * 60)
    
    # Return exit code
    if failed == 0:
        print("\n✅ 所有文档摄取完成！")
        return 0
    elif successful > 0:
        print("\n⚠️  部分文档摄取失败")
        return 1
    else:
        print("\n❌ 所有文档摄取失败")
        return 2


if __name__ == "__main__":
    sys.exit(main())
