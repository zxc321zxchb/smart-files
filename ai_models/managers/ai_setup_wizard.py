#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI设置向导 - 提供用户友好的AI功能配置界面
"""

import os
import sys
import time
import threading
from typing import Dict, Callable

class AISetupWizard:
    """AI设置向导"""
    
    def __init__(self):
        self.download_manager = None
        self.setup_complete = False
    
    def show_welcome(self):
        """显示欢迎界面"""
        print("\n" + "="*70)
        print("🚀 智能文件保存系统 - AI功能设置向导")
        print("="*70)
        print("欢迎使用智能文件保存系统！")
        print()
        print("本系统提供两种相似度检测模式：")
        print("📊 基础模式：基于文本特征的快速相似度检测")
        print("🤖 AI模式：基于深度学习的智能语义相似度检测")
        print()
        print("AI模式优势：")
        print("  • 更准确的语义理解")
        print("  • 支持多语言文档")
        print("  • 智能内容匹配")
        print("  • 提升搜索体验")
        print()
        print("="*70)
    
    def check_current_status(self) -> Dict:
        """检查当前AI状态"""
        try:
            from .model_manager import get_model_manager
            manager = get_model_manager()
            status = manager.get_model_status()
            
            print("🔍 检查当前AI环境状态...")
            print(f"   AI依赖可用: {'✅' if status['ai_dependencies_available'] else '❌'}")
            print(f"   模型文件状态: {status['model_files_status']}")
            print(f"   完整AI功能: {'✅' if status['all_ready'] else '❌'}")
            
            return status
        except Exception as e:
            print(f"   ⚠️  检查状态失败: {e}")
            return {'all_ready': False}
    
    def ask_user_choice(self) -> str:
        """询问用户选择"""
        print("\n" + "="*50)
        print("请选择您希望的操作：")
        print("="*50)
        print("1. 🚀 启用AI功能（推荐）")
        print("   - 下载AI模型（约90MB）")
        print("   - 享受智能相似度检测")
        print()
        print("2. 📊 继续使用基础模式")
        print("   - 使用文本特征相似度检测")
        print("   - 无需下载额外文件")
        print()
        print("3. ❓ 了解更多信息")
        print("   - 查看详细功能对比")
        print()
        print("4. 🚪 退出向导")
        print("="*50)
        
        while True:
            try:
                choice = input("\n请输入选项编号 (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    return choice
                else:
                    print("❌ 请输入有效的选项编号 (1-4)")
            except KeyboardInterrupt:
                print("\n\n❌ 用户取消操作")
                return '4'
    
    def show_detailed_info(self):
        """显示详细信息"""
        print("\n" + "="*60)
        print("📋 功能详细对比")
        print("="*60)
        print("┌─────────────────┬─────────────────┬─────────────────┐")
        print("│     功能特性    │    基础模式     │     AI模式      │")
        print("├─────────────────┼─────────────────┼─────────────────┤")
        print("│ 相似度检测精度  │     中等        │      高         │")
        print("│ 语义理解能力   │     基础        │      强         │")
        print("│ 多语言支持     │     有限        │      优秀       │")
        print("│ 处理速度       │     快速        │      中等       │")
        print("│ 资源占用       │     低          │      中等       │")
        print("│ 网络要求       │     无          │      首次需要   │")
        print("│ 存储空间       │     小          │      +90MB      │")
        print("└─────────────────┴─────────────────┴─────────────────┘")
        print()
        print("💡 建议：")
        print("  • 如果您主要处理中文文档，推荐使用AI模式")
        print("  • 如果您需要快速处理大量文档，可选择基础模式")
        print("  • 两种模式可以随时切换，不影响数据")
        print("="*60)
        
        input("\n按回车键返回主菜单...")
    
    def start_ai_setup(self):
        """开始AI设置"""
        print("\n🚀 开始设置AI功能...")
        print("="*50)
        
        try:
            from .ai_download_manager import AIDownloadManager
            self.download_manager = AIDownloadManager()
            
            # 添加进度回调
            self.download_manager.add_progress_callback(self._show_progress)
            
            print("📡 正在准备下载环境...")
            time.sleep(1)
            
            # 开始下载
            success = self.download_manager.download_ai_environment()
            
            if success:
                print("\n✅ AI功能设置完成！")
                print("🎉 智能相似度检测功能已启用")
                self.setup_complete = True
                return True
            else:
                print("\n❌ AI功能设置失败")
                print("💡 您可以稍后重试，或继续使用基础模式")
                return False
                
        except Exception as e:
            print(f"\n❌ 设置过程中出现错误: {e}")
            return False
    
    def _show_progress(self, status: Dict):
        """显示下载进度"""
        progress = status.get('progress', 0)
        current_step = status.get('current_step', '')
        error = status.get('error')
        
        if error:
            print(f"\n❌ 错误: {error}")
            return
        
        # 创建进度条
        bar_length = 30
        filled_length = int(bar_length * progress / 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r🔄 [{bar}] {progress:5.1f}% {current_step}", end='', flush=True)
        
        if status.get('completed', False):
            print()  # 换行
    
    def show_completion_message(self):
        """显示完成消息"""
        print("\n" + "="*60)
        print("🎉 AI功能设置完成！")
        print("="*60)
        print("✅ 智能相似度检测功能已启用")
        print("✅ 模型文件下载完成")
        print("✅ 索引系统已初始化")
        print()
        print("🚀 现在您可以享受：")
        print("  • 更准确的文档相似度检测")
        print("  • 智能语义理解和匹配")
        print("  • 多语言文档支持")
        print("  • 提升的搜索体验")
        print()
        print("💡 提示：")
        print("  • AI功能将在下次启动时自动加载")
        print("  • 您可以通过API查看AI状态")
        print("  • 如有问题，可重新运行此向导")
        print("="*60)
    
    def run_wizard(self):
        """运行设置向导"""
        self.show_welcome()
        
        # 检查当前状态
        status = self.check_current_status()
        
        if status.get('all_ready', False):
            print("\n✅ AI功能已就绪，无需设置")
            return True
        
        while True:
            choice = self.ask_user_choice()
            
            if choice == '1':
                # 启用AI功能
                if self.start_ai_setup():
                    self.show_completion_message()
                    return True
                else:
                    print("\n❌ AI功能设置失败，请重试")
                    continue
                    
            elif choice == '2':
                # 继续使用基础模式
                print("\n📊 将继续使用基础相似度检测模式")
                print("💡 您可以随时重新运行此向导启用AI功能")
                return True
                
            elif choice == '3':
                # 显示详细信息
                self.show_detailed_info()
                continue
                
            elif choice == '4':
                # 退出
                print("\n👋 感谢使用智能文件保存系统！")
                return False


def main():
    """主函数"""
    wizard = AISetupWizard()
    wizard.run_wizard()


if __name__ == '__main__':
    main()
