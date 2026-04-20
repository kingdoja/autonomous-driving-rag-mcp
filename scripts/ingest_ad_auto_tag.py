#!/usr/bin/env python
"""
自动驾驶文档摄取脚本 - 自动标签

这个脚本使用 ADMetadataTagger 自动为文档添加正确的 document_type 元数据标签。

Usage:
    python scripts/ingest_ad_auto_tag.py --path demo-data-ad --collection ad_knowledge_v01
"""

import argparse
import sys
from pathlib import Path
from typing import List

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
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.metadata.ad_metadata_tagger import ADMetadataTagger
from src.observability.logger import get_logger

logger = get_logger(__name__)


def discover_files(path: Path, extensions: List[str] = None) -> List[Path]:
    """Discover files to process from path.
    
    Args:
        path: File or directory path
        extensions: List of file extensions to include (default: ['.pdf', '.txt'])
    
    Returns:
        List of file paths to process
    """
    if extensions is None:
        extensions = ['.pdf', '.txt']
    
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


def main():
    parser = argparse.ArgumentParser(
        description="自动驾驶文档摄取脚本 - 自动添加元数据标签"
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
    
    # 加载配置
    try:
        settings = load_settings(args.config)
        # 覆盖 collection 名称
        if hasattr(settings, 'collection'):
            settings.collection.name = args.collection
    except Exception as e:
        logger.error(f"Failed to load settings: {e}")
        return 2
    
    # 发现文件
    try:
        files = discover_files(Path(args.path))
        logger.info(f"Found {len(files)} files to process")
    except Exception as e:
        logger.error(f"Failed to discover files: {e}")
        return 2
    
    if len(files) == 0:
        logger.warning("No files found to process")
        return 0
    
    # 初始化 ADMetadataTagger
    tagger = ADMetadataTagger()
    
    # 试运行模式：只显示文件和标签
    if args.dry_run:
        print(f"\n{'='*60}")
        print("试运行模式 - 文档标签预览")
        print(f"{'='*60}\n")
        
        for file_path in files:
            metadata = tagger.tag_document(str(file_path))
            if metadata:
                print(f"📄 {file_path.name}")
                print(f"   类型: {metadata.document_type}")
                if metadata.sensor_type:
                    print(f"   传感器类型: {metadata.sensor_type}")
                if metadata.algorithm_type:
                    print(f"   算法类型: {metadata.algorithm_type}")
                if metadata.regulation_type:
                    print(f"   法规类型: {metadata.regulation_type}")
                if metadata.test_type:
                    print(f"   测试类型: {metadata.test_type}")
                print()
            else:
                print(f"⚠️  {file_path.name} - 无法识别类型\n")
        
        print(f"{'='*60}")
        print(f"总计: {len(files)} 个文件")
        print(f"{'='*60}")
        return 0
    
    # 初始化摄取流水线
    try:
        pipeline = IngestionPipeline(settings=settings)
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        return 2
    
    # 处理文件
    print(f"\n🚀 开始摄取自动驾驶文档")
    print(f"   Collection: {args.collection}")
    print(f"   配置文件: {args.config}")
    print(f"   文件数量: {len(files)}")
    print(f"   强制重新处理: {'是' if args.force else '否'}\n")
    
    results = []
    for i, file_path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] 处理: {file_path.name}")
        
        # 使用 ADMetadataTagger 获取元数据
        metadata = tagger.tag_document(str(file_path))
        if metadata:
            metadata_dict = metadata.to_dict()
            if args.verbose:
                print(f"   元数据: {metadata_dict}")
        else:
            metadata_dict = {}
            logger.warning(f"Could not tag document: {file_path}")
        
        # 摄取文档（带元数据）
        try:
            result = pipeline.process_file(
                file_path=str(file_path),
                collection_name=args.collection,
                force=args.force,
                extra_metadata=metadata_dict  # 传递元数据
            )
            results.append(result)
            
            if result.success:
                skipped = result.stages.get("integrity", {}).get("skipped", False)
                if skipped:
                    print(f"   ⏭️  跳过（已处理）")
                else:
                    print(f"   ✅ 成功 ({result.chunk_count} chunks)")
            else:
                print(f"   ❌ 失败: {result.error}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            print(f"   ❌ 失败: {e}")
    
    # 打印摘要
    total = len(results)
    successful = sum(1 for r in results if r.success)
    failed = total - successful
    total_chunks = sum(r.chunk_count for r in results if r.success)
    
    print(f"\n{'='*60}")
    print("摄取摘要")
    print(f"{'='*60}")
    print(f"总文件数: {total}")
    print(f"  ✅ 成功: {successful}")
    print(f"  ❌ 失败: {failed}")
    print(f"\n总 chunks: {total_chunks}")
    print(f"{'='*60}")
    
    # 按文档类型统计
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
        print(f"{'='*60}\n")
    
    # 返回退出码
    if failed == 0:
        print("✅ 所有文档摄取完成！")
        return 0
    elif successful > 0:
        print("⚠️  部分文档摄取失败")
        return 1
    else:
        print("❌ 所有文档摄取失败")
        return 2


if __name__ == "__main__":
    sys.exit(main())
