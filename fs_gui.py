"""
GUI 界面模块 —— PyQt6 深色主题文件系统模拟器
=============================================
布局：工具栏 | 目录树 + 文件列表 | 终端 | 状态栏
"""

from __future__ import annotations

import sys
import os
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView,
    QPlainTextEdit, QLineEdit, QPushButton, QToolBar, QStatusBar, QLabel,
    QMessageBox, QMenu, QFileDialog, QAbstractItemView, QDialog, QFormLayout,
    QDialogButtonBox, QSpinBox, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QKeySequence, QAction, QIcon, QTextOption,
    QSyntaxHighlighter, QTextCharFormat, QFontMetrics, QTextCursor,
)

from fs_core import FileSystem
from fs_commands import CommandParser


# =========================== 全局配色 ===========================

STYLESHEET = """
/* ===== 主窗口 & 通用 ===== */
QMainWindow {
    background-color: #1E1E2E;
}
QWidget {
    background-color: #1E1E2E;
    color: #CDD6F4;
    font-family: "Cascadia Code", "Fira Code", "Consolas", "Microsoft YaHei", monospace;
    font-size: 13px;
}

/* ===== 分割器 ===== */
QSplitter::handle {
    background-color: #45475A;
    width: 2px;
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #89B4FA;
}

/* ===== 树视图 ===== */
QTreeWidget {
    background-color: #1E1E2E;
    color: #CDD6F4;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QTreeWidget::item {
    padding: 4px 6px;
    border-radius: 4px;
}
QTreeWidget::item:hover {
    background-color: #313244;
}
QTreeWidget::item:selected {
    background-color: #45475A;
    color: #89B4FA;
}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
}

/* ===== 表格 ===== */
QTableWidget {
    background-color: #1E1E2E;
    color: #CDD6F4;
    border: 1px solid #313244;
    border-radius: 6px;
    gridline-color: #313244;
    outline: none;
    selection-background-color: #45475A;
    selection-color: #89B4FA;
}
QTableWidget::item {
    padding: 4px 8px;
}
QTableWidget::item:hover {
    background-color: #313244;
}
QHeaderView::section {
    background-color: #11111B;
    color: #89B4FA;
    padding: 6px 8px;
    border: none;
    border-bottom: 2px solid #45475A;
    font-weight: bold;
    font-size: 12px;
}

/* ===== 终端 ===== */
QPlainTextEdit {
    background-color: #0C0C0D;
    color: #A6E3A1;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px;
    font-family: "Consolas", "Microsoft YaHei", monospace;
    font-size: 13px;
    selection-background-color: #45475A;
}
QLineEdit {
    background-color: #0C0C0D;
    color: #89B4FA;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    font-size: 13px;
    selection-background-color: #45475A;
}
QLineEdit:focus {
    border-color: #89B4FA;
}

/* ===== 按钮 ===== */
QPushButton {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background-color: #45475A;
    border-color: #89B4FA;
}
QPushButton:pressed {
    background-color: #585B70;
}
QPushButton#runBtn {
    background-color: #89B4FA;
    color: #1E1E2E;
    border: none;
}
QPushButton#runBtn:hover {
    background-color: #B4D0FB;
}

/* ===== 工具栏 ===== */
QToolBar {
    background-color: #11111B;
    border-bottom: 2px solid #313244;
    padding: 4px 8px;
    spacing: 6px;
}
QToolBar QPushButton {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: bold;
}
QToolBar QPushButton:hover {
    background-color: #45475A;
    border-color: #89B4FA;
}

/* ===== 状态栏 ===== */
QStatusBar {
    background-color: #11111B;
    color: #A6ADC8;
    border-top: 2px solid #313244;
    padding: 2px 10px;
    font-size: 12px;
}

/* ===== 滚动条 ===== */
QScrollBar:vertical {
    background-color: #1E1E2E;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #45475A;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #585B70;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ===== 菜单 ===== */
QMenu {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    padding: 4px;
    border-radius: 6px;
}
QMenu::item {
    padding: 6px 28px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #45475A;
    color: #89B4FA;
}
QMenu::separator {
    height: 1px;
    background-color: #45475A;
    margin: 4px 8px;
}

/* ===== 对话框 ===== */
QDialog {
    background-color: #1E1E2E;
    color: #CDD6F4;
}
QDialog QLabel {
    color: #CDD6F4;
}
QDialog QLineEdit, QDialog QSpinBox {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 4px;
    padding: 4px 8px;
}
QDialog QTextEdit {
    background-color: #313244;
    color: #CDD6F4;
    border: 1px solid #45475A;
    border-radius: 4px;
    padding: 4px 8px;
}
"""


# =========================== 终端语法高亮 ===========================

class TerminalHighlighter(QSyntaxHighlighter):
    """终端输出的轻量语法高亮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = [
            (r'^❌.*$',        QColor('#F38BA8')),            # 错误 → 红
            (r'^✅.*$',        QColor('#A6E3A1')),            # 成功 → 绿
            (r'^> .*$',        QColor('#89B4FA')),            # 提示 → 蓝
            (r'^(───|===|---)', QColor('#6C7086')),           # 分隔线 → 灰
            (r'📁|📄',         QColor('#F9E2AF')),            # 图标 → 黄
            (r'📁',            QColor('#89DCEB')),            # 目录图标 → 青
        ]

    def highlightBlock(self, text: str) -> None:
        import re
        for pattern, color in self._rules:
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# =========================== 主窗口 ===========================

class MainWindow(QMainWindow):
    """文件系统模拟器主窗口"""

    def __init__(self) -> None:
        super().__init__()
        self.fs = FileSystem()
        self.cmd = CommandParser(self.fs)
        self._history: list[str] = []
        self._history_idx = -1
        self._current_tree_path: str = '/'   # 树视图中选中项的完整路径

        # 初始化 / 恢复
        loaded = False
        try:
            loaded = self.fs.load('filesystem.img')
        except OSError:
            pass  # 损坏的文件 → 静默格式化
        if not loaded:
            self.fs.format()
            # 预置目录结构
            self._init_demo()

        self._setup_ui()
        self._apply_style()
        self._refresh_all()
        self._update_status()

    # ====================== 预置演示数据 ==========================

    def _init_demo(self) -> None:
        """创建演示用的目录和文件"""
        dirs = ['home', 'home/documents', 'home/downloads', 'home/pictures',
                'etc', 'tmp', 'usr', 'usr/bin', 'usr/lib']
        for d in dirs:
            parts = d.split('/')
            for i in range(len(parts)):
                sub = '/'.join(parts[:i+1])
                try:
                    self.fs.make_dir(sub)
                except Exception:
                    pass  # 可能已存在

        files = {
            'home/documents/readme.txt': b'Welcome to File System Simulator!\nThis is a FAT-like file system.\n',
            'home/documents/notes.txt': b'TODO List:\n1. Learn file systems\n2. Build a simulator\n3. Have fun!\n',
            'etc/config.ini': b'[settings]\ntheme=dark\nfont=monospace\n',
            'home/downloads/hello.py': b'print("Hello, World!")\n',
            'tmp/log.txt': b'[2024-01-15 10:30:00] System started\n[2024-01-15 10:31:00] All systems nominal\n',
        }
        for path, content in files.items():
            try:
                self.fs.create_file(path, len(content))
                self.fs.write_file(path, content)
            except Exception:
                pass

        self.fs.change_dir('/')

    # ====================== UI 构建 ==========================

    def _setup_ui(self) -> None:
        self.setWindowTitle('文件系统模拟器 — FAT File System Simulator')
        self.setMinimumSize(1100, 720)
        self.resize(1280, 820)

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(6, 0, 6, 6)
        root_layout.setSpacing(0)

        # ---- 工具栏 ----
        self._setup_toolbar()
        root_layout.addWidget(self._toolbar)

        # ---- 主分割器（上下） ----
        self._main_splitter = QSplitter(Qt.Orientation.Vertical)
        root_layout.addWidget(self._main_splitter, 1)

        # ---- 上半部：目录树 + 文件列表 ----
        top_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.addWidget(top_splitter)

        # 目录树
        self._tree = QTreeWidget()
        self._tree.setHeaderLabel('目录结构')
        self._tree.setIndentation(18)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._tree_context_menu)
        self._tree.itemClicked.connect(self._on_tree_item_clicked)
        self._tree.itemExpanded.connect(lambda _: self._refresh_tree())
        top_splitter.addWidget(self._tree)

        # 文件列表表格
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(['名称', '类型', '大小', '修改时间'])
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._table_context_menu)
        self._table.doubleClicked.connect(self._on_table_double_click)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        top_splitter.addWidget(self._table)

        top_splitter.setSizes([300, 700])

        # ---- 下半部：终端 ----
        terminal_widget = QWidget()
        terminal_layout = QVBoxLayout(terminal_widget)
        terminal_layout.setContentsMargins(0, 8, 0, 0)
        terminal_layout.setSpacing(6)

        self._terminal = QPlainTextEdit()
        self._terminal.setReadOnly(True)
        self._terminal.setMaximumBlockCount(2000)
        self._terminal.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        self._terminal.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self._highlighter = TerminalHighlighter(self._terminal.document())
        terminal_layout.addWidget(self._terminal)

        # 输入行
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._prompt = QLabel('$')
        self._prompt.setStyleSheet('color: #89B4FA; font-weight: bold; font-size: 14px; background: transparent;')
        self._input = QLineEdit()
        self._input.setPlaceholderText('输入命令，如 ls, mkdir, create, help …')
        self._input.returnPressed.connect(self._execute_command)
        self._run_btn = QPushButton('▶  执行')
        self._run_btn.setObjectName('runBtn')
        self._run_btn.clicked.connect(self._execute_command)
        self._clear_btn = QPushButton('清空终端')
        self._clear_btn.clicked.connect(self._terminal.clear)

        input_row.addWidget(self._prompt)
        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._run_btn)
        input_row.addWidget(self._clear_btn)
        terminal_layout.addLayout(input_row)

        self._main_splitter.addWidget(terminal_widget)
        self._main_splitter.setSizes([440, 280])

        # ---- 状态栏 ----
        self._status = QStatusBar()
        self._path_label = QLabel()
        self._path_label.setStyleSheet('color: #89B4FA; font-weight: bold; background: transparent;')
        self._disk_label = QLabel()
        self._disk_label.setStyleSheet('color: #A6ADC8; background: transparent;')
        self._status.addWidget(self._path_label, 1)
        self._status.addPermanentWidget(self._disk_label)
        self.setStatusBar(self._status)

        # 定时刷新磁盘信息
        self._disk_timer = QTimer()
        self._disk_timer.timeout.connect(self._update_status)
        self._disk_timer.start(5000)

        # 焦点策略
        self._input.setFocus()

    def _setup_toolbar(self) -> None:
        self._toolbar = QToolBar('工具栏')
        self._toolbar.setMovable(False)
        self._toolbar.setIconSize(QSize(18, 18))

        actions = [
            ('🔄 格式化', self._action_format),
            ('📁 创建目录', self._action_mkdir),
            ('📄 创建文件', self._action_create),
            ('🗑  删除', self._action_delete),
            ('📋 复制', self._action_copy),
            ('✏️  重命名', self._action_rename),
            ('🔍 搜索', self._action_find),
            ('📊 磁盘', self._action_df),
            ('💾 保存', self._action_save),
            ('📂 加载', self._action_load),
        ]
        for text, slot in actions:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            self._toolbar.addWidget(btn)

        self._toolbar.addSeparator()
        up_btn = QPushButton('⬆ 上级')
        up_btn.clicked.connect(self._go_parent)
        self._toolbar.addWidget(up_btn)
        refresh_btn = QPushButton('🔄 刷新')
        refresh_btn.clicked.connect(self._refresh_all)
        self._toolbar.addWidget(refresh_btn)

        path_label = QLabel('  📍 ')
        path_label.setStyleSheet('color: #A6ADC8; background: transparent;')
        self._toolbar.addWidget(path_label)
        self._toolbar_path = QLabel('/')
        self._toolbar_path.setStyleSheet('color: #89B4FA; font-weight: bold; background: transparent;')
        self._toolbar.addWidget(self._toolbar_path)

    # ====================== 样式 ==========================

    def _apply_style(self) -> None:
        self.setStyleSheet(STYLESHEET)

    # ====================== 刷新逻辑 ==========================

    def _refresh_all(self) -> None:
        self._refresh_tree()
        self._refresh_table()
        self._update_status()
        self._toolbar_path.setText(self.fs.pwd())

    def _refresh_tree(self) -> None:
        # 重建前先记住哪些节点是展开的，否则展开状态会丢失
        expanded = self._collect_expanded_paths()
        self._tree.blockSignals(True)
        self._tree.clear()
        tree_data = self.fs.get_tree()
        root_item = QTreeWidgetItem(['📁 /'])
        root_item.setData(0, Qt.ItemDataRole.UserRole, '/')
        root_item.setData(0, Qt.ItemDataRole.ToolTipRole, '/')
        self._populate_tree(root_item, tree_data.get('children', []))
        self._tree.addTopLevelItem(root_item)
        root_item.setExpanded(True)
        self._apply_expanded_paths(root_item, expanded)
        self._tree.blockSignals(False)

    def _collect_expanded_paths(self) -> set:
        """收集当前所有已展开节点的路径"""
        paths: set = set()
        stack = [self._tree.topLevelItem(i)
                 for i in range(self._tree.topLevelItemCount())]
        while stack:
            item = stack.pop()
            if item is None:
                continue
            if item.isExpanded():
                paths.add(item.data(0, Qt.ItemDataRole.UserRole))
            stack.extend(item.child(i) for i in range(item.childCount()))
        return paths

    def _apply_expanded_paths(self, item: QTreeWidgetItem, paths: set) -> None:
        """按记录的路径恢复展开状态"""
        if item.data(0, Qt.ItemDataRole.UserRole) in paths:
            item.setExpanded(True)
        for i in range(item.childCount()):
            self._apply_expanded_paths(item.child(i), paths)

    def _populate_tree(self, parent: QTreeWidgetItem, children: list[dict]) -> None:
        for child in children:
            if child['type'] == 'dir':
                icon = '📁'
                item = QTreeWidgetItem([f'{icon} {child["name"]}'])
                p = parent.data(0, Qt.ItemDataRole.UserRole)
                full = p.rstrip('/') + '/' + child['name']
                item.setData(0, Qt.ItemDataRole.UserRole, full)
                item.setData(0, Qt.ItemDataRole.ToolTipRole, full)
                self._populate_tree(item, child.get('children', []))
            else:
                icon = '📄'
                item = QTreeWidgetItem([f'{icon} {child["name"]}'])
                p = parent.data(0, Qt.ItemDataRole.UserRole)
                full = p.rstrip('/') + '/' + child['name']
                item.setData(0, Qt.ItemDataRole.UserRole, full)
            parent.addChild(item)

    def _refresh_table(self) -> None:
        self._table.setRowCount(0)
        entries = self.fs.get_dir_details('.')

        # ---- 非根目录时首行插入 ".." 返回上级 ----
        has_parent = (self.fs.pwd() != '/')
        total_rows = len(entries) + (1 if has_parent else 0)
        self._table.setRowCount(total_rows)

        row = 0
        if has_parent:
            # ".." 行
            parent_item = QTableWidgetItem('📂 ..')
            parent_item.setData(Qt.ItemDataRole.UserRole, '..')
            parent_item.setData(Qt.ItemDataRole.ToolTipRole, '返回上级目录')
            parent_item.setForeground(QColor('#89DCEB'))
            font = parent_item.font()
            font.setBold(True)
            parent_item.setFont(font)
            self._table.setItem(0, 0, parent_item)
            self._table.setItem(0, 1, QTableWidgetItem('上级目录'))
            self._table.item(0, 1).setForeground(QColor('#A6ADC8'))
            self._table.setItem(0, 2, QTableWidgetItem('-'))
            self._table.item(0, 2).setForeground(QColor('#A6ADC8'))
            self._table.setItem(0, 3, QTableWidgetItem('-'))
            self._table.item(0, 3).setForeground(QColor('#6C7086'))
            row = 1

        for i, e in enumerate(entries):
            row = i + (1 if has_parent else 0)
            # 名称
            icon = '📁 ' if e['type'] == 'dir' else '📄 '
            name_item = QTableWidgetItem(f'{icon} {e["name"]}')
            name_item.setData(Qt.ItemDataRole.UserRole, e['name'])
            name_item.setData(Qt.ItemDataRole.ToolTipRole,
                              self.fs.pwd().rstrip('/') + '/' + e['name'])
            if e['type'] == 'dir':
                name_item.setForeground(QColor('#89DCEB'))
            else:
                name_item.setForeground(QColor('#F9E2AF'))
            self._table.setItem(row, 0, name_item)

            # 类型
            t = '目录' if e['type'] == 'dir' else '文件'
            type_item = QTableWidgetItem(t)
            type_item.setForeground(QColor('#A6ADC8'))
            self._table.setItem(row, 1, type_item)

            # 大小
            sz_item = QTableWidgetItem(e['size_str'])
            sz_item.setForeground(QColor('#A6ADC8'))
            sz_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 2, sz_item)

            # 时间
            tm_item = QTableWidgetItem(e['modify_time'])
            tm_item.setForeground(QColor('#6C7086'))
            self._table.setItem(row, 3, tm_item)

    def _update_status(self) -> None:
        self._path_label.setText(f'📂 {self.fs.pwd()}')
        total, used, free = self.fs.disk_usage()
        pct = used / total * 100 if total > 0 else 0
        self._disk_label.setText(
            f'磁盘: {self.fs._fmt_size(used)} / {self.fs._fmt_size(total)} ({pct:.1f}%)  '
            f'空闲: {self.fs._fmt_size(free)}'
        )

    # ====================== 交互 ==========================

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        # 根目录特殊处理：_resolve_entry 对 "/" 会抛异常
        if path == '/':
            self.fs.change_dir('/')
            self._refresh_all()
            return
        try:
            _, entry = self.fs._resolve_entry(path)
            if entry.is_dir:
                self.fs.change_dir(path)
                self._refresh_all()
        except Exception:
            pass

    def _on_table_double_click(self, idx) -> None:
        name = self._table.item(idx.row(), 0).data(Qt.ItemDataRole.UserRole)
        # 处理 ".." 返回上级
        if name == '..':
            self.fs.change_dir('..')
            self._refresh_all()
            return
        entries = self.fs.get_dir_details('.')
        # 计算实际条目索引（跳过可能的 ".." 行）
        has_parent = (self.fs.pwd() != '/')
        entry_idx = idx.row() - (1 if has_parent else 0)
        if 0 <= entry_idx < len(entries):
            e = entries[entry_idx]
            if e['type'] == 'dir':
                self.fs.change_dir(name)
                self._refresh_all()
            else:
                self._show_file_content(name)

    def _execute_command(self) -> None:
        line = self._input.text().strip()
        if line:
            self._history.append(line)
            self._history_idx = len(self._history)
        self._input.clear()

        if not line:
            return

        # 回显
        self._append_terminal(f'> {line}', '#89B4FA')

        output = self.cmd.execute(line)

        if output == '__CLEAR__':
            self._terminal.clear()
        elif output:
            self._append_terminal(output, '#CDD6F4')

        self._refresh_all()
        self._update_status()
        self._input.setFocus()

    def _append_terminal(self, text: str, color: str = '#CDD6F4') -> None:
        """向终端追加带颜色文本（纯文本插入，保留换行与空格对齐）"""
        if not text.endswith('\n'):
            text += '\n'
        cursor = self._terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(text, fmt)
        self._terminal.setTextCursor(cursor)
        # 自动滚到底部
        bar = self._terminal.verticalScrollBar()
        bar.setValue(bar.maximum())

    @staticmethod
    def _escape_html(text: str) -> str:
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def keyPressEvent(self, event) -> None:
        """全局快捷键"""
        if event.key() == Qt.Key.Key_F5:
            self._refresh_all()
        elif event.key() == Qt.Key.Key_Backspace:
            self._go_parent()
        elif event.key() == Qt.Key.Key_L and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._terminal.clear()
        elif event.key() == Qt.Key.Key_Escape:
            self._input.clear()
            self._input.setFocus()
        else:
            super().keyPressEvent(event)

    # ====================== 右键菜单 ==========================

    def _tree_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if not item:
            return
        path = item.data(0, Qt.ItemDataRole.UserRole) or '/'
        menu = QMenu(self)
        menu.addAction('📂 打开目录', lambda: self._nav_to(path))
        menu.addAction('📋 复制路径', lambda: self._copy_to_clipboard(path))
        menu.addSeparator()
        menu.addAction('📁 在此创建目录', lambda: self._mkdir_dialog(path))
        menu.addAction('📄 在此创建文件', lambda: self._create_dialog(path))
        menu.exec(self._tree.viewport().mapToGlobal(pos))

    def _table_context_menu(self, pos) -> None:
        row = self._table.rowAt(pos.y())
        if row < 0:
            menu = QMenu(self)
            menu.addAction('📁 创建目录', self._action_mkdir)
            menu.addAction('📄 创建文件', self._action_create)
            menu.exec(self._table.viewport().mapToGlobal(pos))
            return

        name = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        # ".." 行不弹出上下文菜单
        if name == '..':
            return
        entries = self.fs.get_dir_details('.')
        has_parent = (self.fs.pwd() != '/')
        entry_idx = row - (1 if has_parent else 0)
        if entry_idx < 0 or entry_idx >= len(entries):
            return
        e = entries[entry_idx]
        is_dir = e['type'] == 'dir'

        menu = QMenu(self)
        if is_dir:
            menu.addAction('📂 进入目录', lambda: self._nav_to(name))
        else:
            menu.addAction('📖 查看内容', lambda: self._show_file_content(name))
            menu.addAction('📝 编辑文件', lambda: self._edit_file_dialog(name))

        menu.addAction('ℹ️  详细信息', lambda: self._show_stat(name))
        menu.addSeparator()
        menu.addAction('📋 复制', lambda: self._copy_file_dialog(name))
        menu.addAction('✏️  重命名', lambda: self._rename_dialog(name))
        menu.addSeparator()
        menu.addAction('🗑  删除', lambda: self._delete_item(name, is_dir))
        menu.exec(self._table.viewport().mapToGlobal(pos))

    # ====================== 对话框 ==========================

    def _mkdir_dialog(self, parent_path: str = '.') -> None:
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, '创建目录', '目录名称:',
            text='')
        if ok and name:
            try:
                full = (parent_path.rstrip('/') + '/' + name) if parent_path != '.' else name
                self.fs.make_dir(full)
                self._refresh_all()
                self._append_terminal(f'✅ 目录已创建: {full}', '#A6E3A1')
            except Exception as ex:
                self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _create_dialog(self, parent_path: str = '.') -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle('创建文件')
        layout = QFormLayout(dlg)
        name_edit = QLineEdit()
        size_spin = QSpinBox()
        size_spin.setRange(0, 1024 * 1024)
        size_spin.setSuffix(' 字节')
        size_spin.setValue(0)
        layout.addRow('文件名:', name_edit)
        layout.addRow('大小:', size_spin)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted and name_edit.text():
            try:
                full = (parent_path.rstrip('/') + '/' + name_edit.text()) if parent_path != '.' else name_edit.text()
                self.fs.create_file(full, size_spin.value())
                self._refresh_all()
                self._append_terminal(f'✅ 文件已创建: {full}', '#A6E3A1')
            except Exception as ex:
                self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _delete_item(self, name: str, is_dir: bool) -> None:
        confirm = QMessageBox.question(
            self, '确认删除',
            f'确定要删除 "{name}" 吗？\n此操作不可恢复。',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            if is_dir:
                self.fs.remove_dir(name)
            else:
                self.fs.delete_file(name)
            self._refresh_all()
            self._append_terminal(f'✅ 已删除: {name}', '#A6E3A1')
        except Exception as ex:
            self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _show_file_content(self, name: str) -> None:
        try:
            data = self.fs.read_file(name)
            text = data.decode('utf-8', errors='replace')
            self._append_terminal(f'--- {name} ({self.fs._fmt_size(len(data))}) ---', '#6C7086')
            self._append_terminal(text, '#F9E2AF')
            self._append_terminal('--- EOF ---', '#6C7086')
        except Exception as ex:
            self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _show_stat(self, name: str) -> None:
        output = self.cmd.execute(f'stat {name}')
        self._append_terminal(output, '#CDD6F4')

    def _edit_file_dialog(self, name: str) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle(f'编辑文件: {name}')
        dlg.resize(600, 400)
        layout = QVBoxLayout(dlg)
        edit = QTextEdit()
        try:
            data = self.fs.read_file(name)
            edit.setPlainText(data.decode('utf-8', errors='replace'))
        except Exception as ex:
            self._append_terminal(f'❌ {ex}', '#F38BA8')
            return
        layout.addWidget(edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self.fs.write_file(name, edit.toPlainText().encode('utf-8'), offset=0)
                self._refresh_all()
                self._append_terminal(f'✅ 文件已保存: {name}', '#A6E3A1')
            except Exception as ex:
                self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _copy_file_dialog(self, name: str) -> None:
        from PyQt6.QtWidgets import QInputDialog
        dst, ok = QInputDialog.getText(
            self, '复制文件', f'复制 "{name}" 到:',
            text=name + '.bak')
        if ok and dst:
            try:
                self.fs.copy_file(name, dst)
                self._refresh_all()
                self._append_terminal(f'✅ 已复制: {name} → {dst}', '#A6E3A1')
            except Exception as ex:
                self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _rename_dialog(self, name: str) -> None:
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, '重命名', f'将 "{name}" 重命名为:',
            text=name)
        if ok and new_name and new_name != name:
            try:
                self.fs.move_file(name, new_name)
                self._refresh_all()
                self._append_terminal(f'✅ 已重命名: {name} → {new_name}', '#A6E3A1')
            except Exception as ex:
                self._append_terminal(f'❌ {ex}', '#F38BA8')

    # ====================== 工具栏动作 ==========================

    def _nav_to(self, path: str) -> None:
        try:
            self.fs.change_dir(path)
            self._refresh_all()
        except Exception as ex:
            self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _go_parent(self) -> None:
        """返回上级目录"""
        if self.fs.pwd() != '/':
            try:
                self.fs.change_dir('..')
                self._refresh_all()
            except Exception as ex:
                self._append_terminal(f'❌ {ex}', '#F38BA8')

    def _copy_to_clipboard(self, text: str) -> None:
        QApplication.clipboard().setText(text)
        self._append_terminal(f'✅ 已复制到剪贴板: {text}', '#A6E3A1')

    def _action_format(self) -> None:
        confirm = QMessageBox.warning(
            self, '格式化确认',
            '格式化将清空文件系统所有数据！\n确定要继续吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.fs.format()
            self._init_demo()
            self._refresh_all()
            self._append_terminal('✅ 文件系统已格式化并恢复演示数据。', '#A6E3A1')

    def _action_mkdir(self) -> None:
        self._mkdir_dialog()

    def _action_create(self) -> None:
        self._create_dialog()

    def _action_delete(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            name = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if name == '..':
                self._append_terminal('❌ 不能删除上级目录。', '#F38BA8')
                return
            entries = self.fs.get_dir_details('.')
            has_parent = (self.fs.pwd() != '/')
            entry_idx = row - (1 if has_parent else 0)
            if 0 <= entry_idx < len(entries):
                e = entries[entry_idx]
                self._delete_item(e['name'], e['type'] == 'dir')
        else:
            self._append_terminal('❌ 请先选中要删除的文件或目录。', '#F38BA8')

    def _action_copy(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            name = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if name == '..':
                self._append_terminal('❌ 不能复制上级目录。', '#F38BA8')
                return
            entries = self.fs.get_dir_details('.')
            has_parent = (self.fs.pwd() != '/')
            entry_idx = row - (1 if has_parent else 0)
            if 0 <= entry_idx < len(entries):
                self._copy_file_dialog(entries[entry_idx]['name'])
        else:
            self._append_terminal('❌ 请先选中要复制的文件。', '#F38BA8')

    def _action_rename(self) -> None:
        row = self._table.currentRow()
        if row >= 0:
            name = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if name == '..':
                self._append_terminal('❌ 不能重命名上级目录。', '#F38BA8')
                return
            entries = self.fs.get_dir_details('.')
            has_parent = (self.fs.pwd() != '/')
            entry_idx = row - (1 if has_parent else 0)
            if 0 <= entry_idx < len(entries):
                self._rename_dialog(entries[entry_idx]['name'])
        else:
            self._append_terminal('❌ 请先选中要重命名的项目。', '#F38BA8')

    def _action_find(self) -> None:
        from PyQt6.QtWidgets import QInputDialog
        pattern, ok = QInputDialog.getText(
            self, '搜索文件', '搜索模式（支持部分匹配）:',
            text='')
        if ok and pattern:
            results = self.fs.search_files(pattern)
            if results:
                self._append_terminal(f'--- 搜索结果: "{pattern}" ---', '#6C7086')
                for r in results:
                    self._append_terminal(r, '#CDD6F4')
            else:
                self._append_terminal(f'未找到匹配 "{pattern}" 的文件。', '#A6ADC8')

    def _action_df(self) -> None:
        output = self.cmd.execute('df')
        self._append_terminal(output, '#CDD6F4')

    def _action_save(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, '保存文件系统', 'filesystem.img', '磁盘映像 (*.img);;所有文件 (*)')
        if filename:
            self.fs.save(filename)
            self._append_terminal(f'✅ 已保存到 {filename}', '#A6E3A1')

    def _action_load(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, '加载文件系统', '', '磁盘映像 (*.img);;所有文件 (*)')
        if filename:
            try:
                if self.fs.load(filename):
                    self._refresh_all()
                    self._append_terminal(f'✅ 已从 {filename} 加载。', '#A6E3A1')
                else:
                    self._append_terminal(f'❌ 文件不存在: {filename}', '#F38BA8')
            except OSError as e:
                self._append_terminal(f'❌ {e}', '#F38BA8')
                # 询问是否格式化
                reply = QMessageBox.question(
                    self, '加载失败',
                    f'无法加载磁盘映像:\n{e}\n\n是否格式化并使用新的文件系统？',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    self.fs.format()
                    self._init_demo()
                    self._refresh_all()

    # ====================== 关闭事件 ==========================

    def closeEvent(self, event) -> None:
        """窗口关闭时自动保存"""
        try:
            self.fs.save('filesystem.img')
        except Exception:
            pass
        event.accept()


# =========================== 入口 ===========================

def run_gui() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName('FAT File System Simulator')
    app.setStyle('Fusion')  # 跨平台一致性

    # Dark palette 兜底
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor('#1E1E2E'))
    palette.setColor(QPalette.ColorRole.WindowText, QColor('#CDD6F4'))
    palette.setColor(QPalette.ColorRole.Base, QColor('#1E1E2E'))
    palette.setColor(QPalette.ColorRole.Text, QColor('#CDD6F4'))
    palette.setColor(QPalette.ColorRole.Button, QColor('#313244'))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor('#CDD6F4'))
    palette.setColor(QPalette.ColorRole.Highlight, QColor('#89B4FA'))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#1E1E2E'))
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    run_gui()
