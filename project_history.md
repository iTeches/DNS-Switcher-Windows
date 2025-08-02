# DNS Switcher 项目开发历史记录

## 问题修复
1. **编码问题修复**：在 `dns_switcher.py` 和 `dns_switcher_gui.py` 中实现了 `run_command_with_encoding` 函数，解决了中文显示问题
2. **缩进错误修复**：修复了 `dns_switcher_gui.py` 中第172行的缩进错误，确保 `try:` 语句正确缩进在 `if` 条件块内

## 功能增强
1. **GUI 版本增强**：
   - 添加了刷新网络适配器列表按钮
   - 实现了 `refresh_adapters` 方法来重新加载适配器
   - 改进了 `populate_adapter_dropdown` 方法，在刷新时保留当前选择或显示提示信息
2. **CLI 版本增强**：
   - 添加了重新选择网络适配器的选项（选项8）
   - 将退出选项调整为选项9
   - 实现了适配器刷新和重新选择的逻辑

## 项目打包
1. 删除了旧的构建目录和文件
2. 重新打包了 CLI 版本 (`dns_switcher.exe`)
3. 重新打包了 GUI 版本 (`dns_switcher_gui.exe`)
4. 创建了 `run_gui_as_admin.bat` 批处理文件，方便以管理员身份运行 GUI 版本并管理日志

## 项目清理
1. 删除了日志文件：`error.log`, `error_new.log`, `output.log`, `output_new.log`
2. 删除了测试文件：`test_dns_encoding_fix.py`, `test_dns_switcher.bat`, `test_gui_dns_encoding_fix.bat`, `test_gui_final.bat`, `test_gui_fix.bat`, `test_improved_dns_switcher.bat`, `test_wmic.bat`
3. 删除了旧批处理文件：`dns_switcher.bat`, `dns_switcher_gui.bat`
4. 删除了 PyInstaller 配置文件：`dns_switcher.spec`, `dns_switcher_gui.spec`
5. 删除了构建目录：`build`

## 文档完善
1. 更新了 `README.md`，添加了新功能说明
2. 更新了使用方法，包括新的批处理文件和选项
3. 修正了过时的信息
4. 添加了编译可执行文件的说明

## 开源准备
1. 创建了 `.gitignore` 文件，指定了需要忽略的文件和目录
2. 提供了上传到 GitHub 的详细步骤指南

## 最终项目结构
- 源代码: `dns_switcher.py`, `dns_switcher_gui.py`
- 批处理文件: `run_dns_switcher.bat`, `run_gui_as_admin.bat`
- 依赖文件: `requirements.txt`
- 文档: `README.md`, `project_history.md`
- Git 忽略文件: `.gitignore`
- 可执行文件目录: `dist`