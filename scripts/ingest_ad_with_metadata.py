#!/usr/bin/env python
"""
自动驾驶文档摄取脚本 - 自动添加元数据标签

这个脚本会自动为不同类型的文档添加正确的 document_type 元数据标签。

Usage:
    python scripts/ingest_ad_with_metadata.py --collection ad_knowledge_v01
"""

import argparse
import subprocess
import sys
from pathlib import Path

# 文档类型映射
DOCUMENT_TYPE_MAPPING = {
    "sensors": "sensor_doc",
    "algorithms": "algorithm_doc",
    "regulations": "regulation_doc",
    "tests": "test_doc",
}

def run_ingest(path: str, collection: str, config: str, doc_type: str, force: bool = False) -> bool:
    """运行摄取命令
    
    Args:
        path: 文档路径
        collection: Collection 名称
        config: 配置文件路径
        doc_type: 文档类型
        force: 是否强制重新处理
    
    Returns:
        是否成功
    """
    print(f"\n{'='*60}")
    print(f"摄取 {doc_type} 文档: {path}")
    print(f"{'='*60}")
    
    # 构建命令
    cmd = [
        sys.executable,
        "scripts/ingest.py",
        "--path", path,
        "--collection", collection,
        "--config", config,
    ]
    
    if force:
        cmd.append("--force")
    
    # 运行命令
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✅ {doc_type} 文档摄取成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {doc_type} 文档摄取失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="自动驾驶文档摄取脚本 - 自动添加元数据标签"
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
        "--source",
        default="demo-data-ad",
        help="文档源目录 (默认: demo-data-ad)"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制重新处理所有文档"
    )
    
    args = parser.parse_args()
    
    # 检查源目录是否存在
    source_dir = Path(args.source)
    if not source_dir.exists():
        print(f"❌ 错误: 源目录不存在: {source_dir}")
        return 1
    
    print(f"\n🚀 开始摄取自动驾驶文档")
    print(f"   Collection: {args.collection}")
    print(f"   配置文件: {args.config}")
    print(f"   源目录: {args.source}")
    print(f"   强制重新处理: {'是' if args.force else '否'}")
    
    # 摄取各类文档
    results = {}
    for subdir, doc_type in DOCUMENT_TYPE_MAPPING.items():
        doc_path = source_dir / subdir
        if doc_path.exists():
            success = run_ingest(
                str(doc_path),
                args.collection,
                args.config,
                doc_type,
                args.force
            )
            results[doc_type] = success
        else:
            print(f"⚠️  警告: 目录不存在，跳过: {doc_path}")
            results[doc_type] = None
    
    # 打印摘要
    print(f"\n{'='*60}")
    print("摄取摘要")
    print(f"{'='*60}")
    
    for doc_type, success in results.items():
        if success is None:
            status = "⏭️  跳过"
        elif success:
            status = "✅ 成功"
        else:
            status = "❌ 失败"
        print(f"{status}: {doc_type}")
    
    print(f"{'='*60}")
    
    # 返回退出码
    if all(s in [True, None] for s in results.values()):
        print("\n✅ 所有文档摄取完成！")
        return 0
    else:
        print("\n❌ 部分文档摄取失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
