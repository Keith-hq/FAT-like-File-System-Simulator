"""生成设计方案文档 —— 清晰简洁版"""

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import datetime

doc = Document()

# ===================== 页面设置 =====================
for section in doc.sections:
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

# ===================== 样式 =====================
style = doc.styles['Normal']
style.font.name = '微软雅黑'
style.font.size = Pt(10.5)
style.font.color.rgb = RGBColor(0x1E, 0x1E, 0x2E)
style.paragraph_format.line_spacing = 1.4
style.paragraph_format.space_after = Pt(4)
rPr = style.element.get_or_add_rPr()
rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:eastAsia="微软雅黑" w:ascii="Consolas" w:hAnsi="Consolas"/>')
rPr.insert(0, rFonts)

for level in range(1, 4):
    h = doc.styles[f'Heading {level}']
    h.font.color.rgb = RGBColor(0x1E, 0x1E, 0x2E)
    h.font.bold = True
    if level == 1:
        h.font.size = Pt(18)
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)
    elif level == 2:
        h.font.size = Pt(14)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
    else:
        h.font.size = Pt(12)
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(4)


# ===================== 工具函数 =====================

def code(text: str, size=Pt(9)):
    """深色背景代码块"""
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    pPr = p._element.get_or_add_pPr()
    pPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="0C0C0D" w:val="clear"/>'))
    run = p.add_run(text)
    run.font.name = 'Consolas'
    run.font.size = size
    run.font.color.rgb = RGBColor(0xA6, 0xE3, 0xA1)
    rPr = run._element.get_or_add_rPr()
    rPr.insert(0, parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Consolas" w:hAnsi="Consolas"/>'))
    return p


def table(headers: list[str], rows: list[list[str]], col_widths=None):
    """带样式的表格"""
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.style = 'Table Grid'
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 表头
    for i, h in enumerate(headers):
        cell = tbl.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        tcPr = cell._element.get_or_add_tcPr()
        tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="313244" w:val="clear"/>'))
    # 数据行
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = tbl.rows[r + 1].cells[c]
            cell.text = str(val)
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
            if r % 2 == 1:
                tcPr = cell._element.get_or_add_tcPr()
                tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="F0F0F5" w:val="clear"/>'))
    doc.add_paragraph()
    return tbl


def bullet(text: str):
    """要点列表"""
    p = doc.add_paragraph(text, style='List Bullet')
    return p


def tip(text: str):
    """提示段落"""
    p = doc.add_paragraph()
    run = p.add_run(f'💡 {text}')
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(0x6C, 0x70, 0x86)
    return p


def key_value(key: str, value: str):
    """键值对段落"""
    p = doc.add_paragraph()
    run = p.add_run(f'{key}：')
    run.font.bold = True
    run.font.size = Pt(10)
    p.add_run(value).font.size = Pt(10)
    return p


# ============================================================
#                         封  面
# ============================================================
for _ in range(5):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('文件系统模拟器')
run.font.size = Pt(34)
run.font.bold = True
run.font.color.rgb = RGBColor(0x1E, 0x1E, 0x2E)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('FAT File System Simulator — 设计方案')
run.font.size = Pt(18)
run.font.color.rgb = RGBColor(0x89, 0xB4, 0xFA)

doc.add_paragraph()
doc.add_paragraph()

for line in [
    f'文档版本：v1.0　　生成日期：{datetime.date.today().strftime("%Y-%m-%d")}',
    '技术栈：Python 3.10+ / PyQt6　　架构：三层分离（核心 → 命令 → GUI）',
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(line)
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x6C, 0x70, 0x86)

doc.add_page_break()

# ============================================================
#                  一、系统概述
# ============================================================
doc.add_heading('一、系统概述', level=1)

doc.add_paragraph(
    '本项目实现了一个类 FAT 文件系统的模拟器，完整模拟超级块、FAT 表（显式链接分配）、'
    '位图、多级目录、文件读写等操作系统文件管理的核心机制。提供 GUI 图形界面和 CLI 命令行两种交互模式。'
)

doc.add_heading('核心参数', level=2)
table(
    ['参数', '值', '说明'],
    [
        ['块大小', '1 KB', '最小读写单元'],
        ['总块数', '1024', '总容量 1 MB'],
        ['FAT 表', '块 1-4（4 KB）', '1024 个 int32 条目'],
        ['根目录', '块 5', '固定起始位置'],
        ['数据区', '块 6-1023', '文件内容 + 子目录'],
        ['文件名上限', '127 字符', 'UTF-8 编码'],
        ['目录项大小', '153 字节', '每块容纳 6 条'],
    ]
)

doc.add_heading('架构分层', level=2)
code(
    '┌─────────────────────────────────────────────┐\n'
    '│  fs_gui.py    GUI 层 — 目录树 / 表格 / 终端  │\n'
    '├─────────────────────────────────────────────┤\n'
    '│  fs_commands.py  命令层 — 文本解析 / 错误处理 │\n'
    '├─────────────────────────────────────────────┤\n'
    '│  fs_core.py   核心层 — FAT / 位图 / 目录 / IO │\n'
    '└─────────────────────────────────────────────┘'
)

doc.add_page_break()

# ============================================================
#                  二、数据结构
# ============================================================
doc.add_heading('二、数据结构', level=1)

doc.add_heading('2.1 超级块（块 0）', level=2)
doc.add_paragraph('记录文件系统全局元信息，共 32 字节有效载荷，小端字节序打包。')

table(
    ['字段', '类型', '说明'],
    [
        ['magic', 'bytes[4]', '魔数 "FSYS"，标识文件系统类型'],
        ['total_blocks', 'uint32', '总块数 1024'],
        ['block_size', 'uint32', '块大小 1024 字节'],
        ['fat_start / fat_blocks', 'uint32 ×2', 'FAT 起始块号(1) 和占用块数(4)'],
        ['root_start', 'uint32', '根目录块号(5)'],
        ['data_start', 'uint32', '数据区起始块号(6)'],
        ['free_blocks', 'uint32', '空闲块计数'],
    ]
)

doc.add_heading('2.2 FAT 表', level=2)
doc.add_paragraph('采用显式链接分配（纯 FAT），每条目 4 字节 int32，共 1024 条。')

table(
    ['取值', '含义'],
    [
        ['-2 (FAT_FREE)', '空闲块'],
        ['-1 (FAT_EOF)', '链尾（文件结束）'],
        ['0 ~ 1023', '指向下一块的块号'],
    ]
)

code(
    '# 示例：3KB 文件，占用块 100 → 200 → 300\n'
    'FAT[100] = 200    FAT[200] = 300    FAT[300] = -1'
)

doc.add_heading('2.3 位图', level=2)
doc.add_paragraph(
    '1024 个布尔值，bitmap[i]=True 表示块 i 已占用。用于 O(n) 快速扫描空闲块，'
    '同时作为 FAT 的冗余校验——不一致时以 FAT 为准。'
)

doc.add_heading('2.4 目录项', level=2)
doc.add_paragraph('每条 153 字节，使用 struct 二进制序列化。空槽以 name[0]==0x00 标记。')

table(
    ['字段', '大小', '类型', '说明'],
    [
        ['name', '128 B', 'bytes', '文件名（UTF-8，\\0 填充）'],
        ['attr', '1 B', 'uint8', '0=文件 / 1=目录'],
        ['first_block', '4 B', 'int32', '起始块号（-1=空文件）'],
        ['size', '4 B', 'uint32', '文件大小（字节）'],
        ['create_time', '8 B', 'float64', '创建时间戳'],
        ['modify_time', '8 B', 'float64', '修改时间戳'],
    ]
)

doc.add_heading('2.5 目录结构', level=2)
doc.add_paragraph('目录是特殊的"文件"，内容为目录项有序序列。每个子目录前两项固定为 "." (自引用) 和 ".." (父引用)。')

code(
    '┌──────────────── 某目录块 ────────────────┐\n'
    '│ [0] .       DIR → self      自引用       │\n'
    '│ [1] ..      DIR → parent    父引用       │\n'
    '│ [2] Docs    DIR → blk 10    子目录       │\n'
    '│ [3] a.txt   FILE → blk 20   文件         │\n'
    '│ [4] (空)    [5] (空)        …            │\n'
    '└─────────────────────────────────────────┘'
)

doc.add_page_break()

# ============================================================
#                  三、核心算法
# ============================================================
doc.add_heading('三、核心算法', level=1)

doc.add_heading('3.1 块分配', level=2)
doc.add_paragraph('从数据区（块 6 起）顺序扫描位图，找到首个空闲块即分配。时间复杂度 O(n)。')
code(
    'for i in [DATA_START .. TOTAL_BLOCKS-1]:\n'
    '    if not bitmap[i]:  bitmap[i]=True; FAT[i]=EOF; return i\n'
    'raise "磁盘空间不足"'
)

doc.add_heading('3.2 文件读取', level=2)
doc.add_paragraph('沿 FAT 链逐块读取，按 offset/length 截取返回。')
code(
    '1. 解析路径 → 获取 DirEntry\n'
    '2. 沿 FAT 链遍历块，累加读取数据\n'
    '3. 返回 data[offset : offset+length]'
)

doc.add_heading('3.3 文件写入', level=2)
doc.add_paragraph('根据新旧大小差异动态调整块链：需要更多块则分配并链接；需要更少则释放多余块并截断链。')
code(
    'if old_blocks < new_blocks: 分配差额块，链接到链尾\n'
    'if old_blocks > new_blocks: 释放多余块，FAT[保留末块]=EOF\n'
    '逐块写入数据 → 更新 DirEntry.size 和 modify_time'
)

doc.add_heading('3.4 路径解析', level=2)
doc.add_paragraph('支持绝对路径(/)、相对路径、"." 和 ".."，混合使用。')
code(
    '1. 判断绝对/相对 → 确定起始目录\n'
    '2. 按 "/" 分拆分量，逐级查找目录项\n'
    '3. 遇到 ".." 回退一级并重新 traverse\n'
    '4. 返回 (分量列表, 目标块号)'
)

doc.add_heading('3.5 持久化策略', level=2)
doc.add_paragraph('采用"临时文件 + 原子替换 + 自动备份"的安全写入模式。')
bullet('先写 .tmp 临时文件 → fsync 刷盘 → os.replace 原子替换')
bullet('旧文件自动重命名为 .bak 备份')
bullet('加载时校验：文件大小 → 魔数 → 各段完整性 → 任一失败则拒绝加载')
bullet('魔数校验失败时自动尝试从 .bak 恢复')

table(
    ['数据段', '大小', '打包方式'],
    [
        ['storage', '1 MB', '所有块原始数据'],
        ['FAT', '4 KB', '1024 × int32 小端'],
        ['bitmap', '1 KB', '1024 × uint8（1=已用）'],
        ['path_len', '4 B', 'uint32 路径长度'],
        ['path', '变长', 'UTF-8 编码'],
    ]
)

doc.add_page_break()

# ============================================================
#                  四、模块设计
# ============================================================
doc.add_heading('四、模块设计', level=1)

doc.add_heading('4.1 fs_core.py — 核心引擎', level=2)

table(
    ['类', '职责', '关键方法数'],
    [
        ['DirEntry', '目录项数据类，含二进制序列化/反序列化', '2'],
        ['OpenFile', '打开文件句柄（路径、偏移、模式）', '—'],
        ['FileSystem', '文件系统主类，约 700 行，封装全部 API', '~40'],
    ]
)

doc.add_paragraph('FileSystem 核心方法：')
table(
    ['分类', '方法'],
    [
        ['初始化', 'format(), _write_super_block()'],
        ['块操作', '_read_block(), _write_block(), _mark_used(), _mark_free()'],
        ['FAT 管理', '_alloc_block(), _free_chain(), _get_chain()'],
        ['目录', '_read_dir_entries(), _find/add/remove/update_dir_entry()'],
        ['路径', '_resolve_path(), _traverse(), _resolve_entry()'],
        ['文件 API', 'create_file, delete_file, read_file, write_file, stat_file'],
        ['目录 API', 'make_dir, remove_dir, list_dir, change_dir, pwd'],
        ['扩展', 'copy_file, move_file, search_files, get_tree, disk_usage'],
        ['持久化', 'save() — 原子写入+备份; load() — 完整性校验+魔数验证'],
    ]
)

doc.add_heading('4.2 fs_commands.py — 命令解析', level=2)
doc.add_paragraph('CommandParser 维护命令注册表（dict），将 20 条文本命令映射到 FileSystem 方法。统一的异常捕获提供中文错误提示。')

table(
    ['方法', '功能'],
    [
        ['execute(line)', '解析一行命令，执行并返回输出'],
        ['_build_table()', '构建 命令名 → (处理函数, 语法, 说明) 的映射'],
    ]
)

doc.add_heading('4.3 fs_gui.py — 图形界面', level=2)
doc.add_paragraph('基于 PyQt6，采用 Catppuccin Mocha 深色主题，主要组件：')

table(
    ['组件', '类型', '功能'],
    [
        ['目录树', 'QTreeWidget', '递归展示目录结构，单击导航'],
        ['文件列表', 'QTableWidget', '当前目录内容（名称/类型/大小/时间）'],
        ['终端', 'QPlainTextEdit', '彩色输出 + 语法高亮'],
        ['命令输入', 'QLineEdit', '输入命令，回车执行'],
        ['工具栏', 'QToolBar', '快捷按钮：格式化/创建/删除/复制/搜索等'],
        ['状态栏', 'QStatusBar', '当前路径 + 磁盘使用量，5秒刷新'],
    ]
)

doc.add_paragraph('交互要点：')
bullet('双击目录进入，双击文件查看内容')
bullet('右键上下文菜单：创建/删除/复制/重命名/编辑/查看详情')
bullet('Backspace / 工具栏按钮 → 返回上级目录')
bullet('关闭窗口自动保存，启动自动恢复')

doc.add_heading('4.4 main.py — 入口', level=2)
code(
    'python main.py               → 启动 GUI\n'
    'python main.py --cli         → 启动命令行模式\n'
    'python main.py --load <file> → 指定磁盘映像'
)

doc.add_page_break()

# ============================================================
#                  五、命令清单
# ============================================================
doc.add_heading('五、命令清单', level=1)

doc.add_heading('基础命令（12 条）', level=2)
table(
    ['命令', '语法', '说明'],
    [
        ['pwd', 'pwd', '显示当前工作目录绝对路径'],
        ['ls', 'ls [-l] [path]', '列出目录；-l 显示详细信息'],
        ['cd', 'cd <path>', '切换目录（支持 . .. / 相对/绝对）'],
        ['mkdir', 'mkdir <name>', '创建目录（自动生成 . 和 ..）'],
        ['rmdir', 'rmdir <name>', '删除空目录（非空则拒绝）'],
        ['create', 'create <name> [size]', '创建文件，可指定初始大小（字节）'],
        ['delete', 'delete <name>', '删除文件并释放所有数据块'],
        ['open', 'open <name>', '打开文件（排他锁）'],
        ['close', 'close <name>', '关闭文件'],
        ['write', 'write <name> <text>', '向文件追加写入文本'],
        ['read', 'read <name> [off] [n]', '从指定偏移读取指定长度'],
        ['stat', 'stat <name>', '显示文件类型/大小/块号/时间'],
    ]
)

doc.add_heading('扩展命令（8 条）', level=2)
table(
    ['命令', '语法', '说明'],
    [
        ['cp', 'cp <src> <dst>', '复制文件（数据块完整拷贝）'],
        ['mv', 'mv <old> <new>', '移动/重命名（共享块链，O(1)）'],
        ['find', 'find <pattern>', '递归搜索匹配模式的文件/目录'],
        ['tree', 'tree', '树形展示完整目录结构'],
        ['df', 'df', '磁盘容量/已用/可用 + 可视化进度条'],
        ['format', 'format', '⚠ 格式化（清空全部数据）'],
        ['save / load', 'save|load [file]', '保存/加载磁盘映像'],
        ['help / clear', 'help|clear', '帮助信息 / 清屏'],
    ]
)

doc.add_page_break()

# ============================================================
#                  六、界面配色方案
# ============================================================
doc.add_heading('六、界面配色方案', level=1)
doc.add_paragraph('采用 Catppuccin Mocha 深色主题，确保视觉舒适与信息层次清晰。')

table(
    ['用途', '色值', '应用场景'],
    [
        ['主背景', '#1E1E2E', '窗口、面板背景'],
        ['二级背景', '#313244', '按钮、输入框、表格行'],
        ['终端背景', '#0C0C0D', '终端输出区域'],
        ['主文字', '#CDD6F4', '正文、标签文本'],
        ['强调色', '#89B4FA', '路径、选中高亮、执行按钮'],
        ['成功色', '#A6E3A1', '成功提示、终端输出'],
        ['错误色', '#F38BA8', '错误提示'],
        ['目录色', '#89DCEB', '目录名称标识'],
        ['文件色', '#F9E2AF', '文件名称标识'],
        ['辅助文字', '#6C7086', '时间戳、次要信息'],
        ['分隔/边框', '#45475A', '边框、分割器手柄'],
        ['工具栏底栏', '#11111B', '工具栏、状态栏背景'],
    ]
)

doc.add_page_break()

# ============================================================
#                  七、测试要点
# ============================================================
doc.add_heading('七、测试要点', level=1)

doc.add_paragraph('核心功能验证覆盖以下场景：')

table(
    ['分类', '测试场景', '预期结果'],
    [
        ['目录', '创建/进入/返回上级', '路径正确切换，根目录不回退越界'],
        ['目录', '删除非空目录', '拒绝删除并报错"目录非空"'],
        ['文件', '创建 → 写入 → 读取', '读写内容完全一致'],
        ['文件', '复制/重命名', '内容一致 / 旧名消失新名出现'],
        ['文件', '删除文件', '文件消失，块被回收 (bitmap/FAT 一致)'],
        ['路径', 'cd /home/../etc', '正确解析混合路径到 /etc'],
        ['磁盘', 'df 显示', '用量/进度条正确'],
        ['磁盘', '创建文件至空间耗尽', '明确提示"磁盘空间不足"'],
        ['持久化', 'save → 重启 → load', '数据完全恢复'],
        ['容错', '加载截断/损坏文件', '明确拒绝并说明原因'],
        ['容错', '加载非 FSYS 文件', '提示"魔数校验失败"'],
        ['容错', '主文件损坏 → .bak', '自动从备份恢复'],
    ]
)

doc.add_paragraph()

# ============================================================
#                      尾  页
# ============================================================
doc.add_page_break()
doc.add_paragraph()
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('— End —')
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x89, 0xB4, 0xFA)
run.font.italic = True

# ===================== 保存 =====================
output_path = '设计方案文档.docx'
doc.save(output_path)
print(f'[OK] 设计方案文档已生成: {output_path}')
