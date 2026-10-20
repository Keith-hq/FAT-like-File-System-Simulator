"""
文件系统核心模块 —— 类 FAT 文件系统实现
============================================
模拟操作系统的文件管理：超级块、FAT 表（显式链接）、位图、多级目录、
文件读写、路径解析、持久化。
"""

from __future__ import annotations

import struct
import time
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# =========================== 常量 ===========================

BLOCK_SIZE      = 1024          # 块大小 1 KB
TOTAL_BLOCKS    = 1024          # 总块数 → 1 MB 总容量
NAME_MAX        = 128           # 文件名最大长度

# ---- 布局（块号）--------------------------------------------
SUPER_BLOCK     = 0             # 超级块
FAT_START       = 1             # FAT 起始块
FAT_BLOCKS      = 4             # FAT 占用块数（1024×4 / 1024 = 4）
ROOT_START      = 5             # 根目录起始块
DATA_START      = 6             # 数据区起始块

# ---- 目录项格式 --------------------------------------------
DIR_ENTRY_SIZE  = 153           # 128(name)+1(attr)+4(first)+4(size)+8(ctime)+8(mtime)
ENTRIES_PER_BLK = BLOCK_SIZE // DIR_ENTRY_SIZE   # 6 条 / 块

# ---- FAT 特殊值 --------------------------------------------
FAT_FREE = -2
FAT_EOF  = -1

# ---- 文件属性 ----------------------------------------------
ATTR_FILE = 0
ATTR_DIR  = 1

# ---- 打包格式字符串 ------------------------------------------
DIR_ENTRY_FMT = '<128sBiIdd'     # name, attr, first_block(signed), size(unsigned), ctime, mtime
SUPER_FMT     = '<4sIIIIIII'     # magic, total_blocks, block_size, fat_start,
                                 # fat_blocks, root_start, data_start, free_blocks

MAGIC = b'FSYS'


# =========================== 数据结构 ===========================

@dataclass
class DirEntry:
    """目录项 —— 描述一个文件或子目录"""
    name: str
    attr: int = ATTR_FILE
    first_block: int = 0
    size: int = 0
    create_time: float = 0.0
    modify_time: float = 0.0

    @property
    def is_dir(self) -> bool:
        return self.attr == ATTR_DIR

    @property
    def is_file(self) -> bool:
        return self.attr == ATTR_FILE

    # ---- 序列化 ------------------------------------------------
    def pack(self) -> bytes:
        name_bytes = self.name.encode('utf-8')[:NAME_MAX - 1]
        name_bytes = name_bytes.ljust(NAME_MAX, b'\x00')
        return struct.pack(DIR_ENTRY_FMT, name_bytes, self.attr,
                           self.first_block, self.size,
                           self.create_time, self.modify_time)

    @staticmethod
    def unpack(data: bytes) -> 'DirEntry':
        name_bytes, attr, first_block, size, ctime, mtime = \
            struct.unpack(DIR_ENTRY_FMT, data)
        name = name_bytes.rstrip(b'\x00').decode('utf-8', errors='replace')
        return DirEntry(name=name, attr=attr, first_block=first_block,
                        size=size, create_time=ctime, modify_time=mtime)


@dataclass
class OpenFile:
    """打开的文件句柄"""
    path: str
    entry: DirEntry
    offset: int = 0
    mode: str = 'r'


# =========================== 文件系统 ===========================

class FileSystem:
    """类 FAT 文件系统 —— 所有数据驻留在内存 bytearray 中"""

    def __init__(self) -> None:
        self.storage = bytearray(BLOCK_SIZE * TOTAL_BLOCKS)
        self.fat: List[int] = [FAT_FREE] * TOTAL_BLOCKS
        self.bitmap: List[bool] = [False] * TOTAL_BLOCKS
        self.current_path: List[str] = []          # 当前路径分量
        self.current_block: int = ROOT_START       # 当前目录块号
        self.open_files: Dict[str, OpenFile] = {}
        self._initialized = False

    # ====================== 格式化 ==========================

    def format(self) -> None:
        """初始化 / 格式化文件系统"""
        self.storage = bytearray(BLOCK_SIZE * TOTAL_BLOCKS)
        self.fat = [FAT_FREE] * TOTAL_BLOCKS
        self.bitmap = [False] * TOTAL_BLOCKS

        # 分配保留区
        self._mark_used(SUPER_BLOCK)
        for i in range(FAT_START, FAT_START + FAT_BLOCKS):
            self._mark_used(i)
        self._mark_used(ROOT_START)
        self.fat[ROOT_START] = FAT_EOF

        self._write_super_block()
        self._clear_block(ROOT_START)

        self.current_path = []
        self.current_block = ROOT_START
        self.open_files.clear()
        self._initialized = True

    def _write_super_block(self) -> None:
        free = sum(1 for b in self.bitmap if not b)
        data = struct.pack(SUPER_FMT, MAGIC, TOTAL_BLOCKS, BLOCK_SIZE,
                           FAT_START, FAT_BLOCKS, ROOT_START, DATA_START, free)
        self._write_block(SUPER_BLOCK, data.ljust(BLOCK_SIZE, b'\x00'))

    def _read_super_block(self) -> bool:
        data = self._read_block(SUPER_BLOCK)
        magic = struct.unpack(SUPER_FMT, data[:struct.calcsize(SUPER_FMT)])[0]
        return magic == MAGIC

    # ====================== 块操作 ==========================

    def _read_block(self, block_no: int) -> bytes:
        if not (0 <= block_no < TOTAL_BLOCKS):
            raise ValueError(f"块号越界: {block_no}")
        start = block_no * BLOCK_SIZE
        return bytes(self.storage[start:start + BLOCK_SIZE])

    def _write_block(self, block_no: int, data: bytes) -> None:
        if not (0 <= block_no < TOTAL_BLOCKS):
            raise ValueError(f"块号越界: {block_no}")
        if len(data) > BLOCK_SIZE:
            raise ValueError(f"数据超出块大小: {len(data)}")
        start = block_no * BLOCK_SIZE
        self.storage[start:start + len(data)] = data

    def _clear_block(self, block_no: int) -> None:
        self._write_block(block_no, b'\x00' * BLOCK_SIZE)

    def _mark_used(self, block_no: int) -> None:
        self.bitmap[block_no] = True
        if self.fat[block_no] == FAT_FREE:
            self.fat[block_no] = FAT_EOF

    def _mark_free(self, block_no: int) -> None:
        self.bitmap[block_no] = False
        self.fat[block_no] = FAT_FREE

    # ====================== FAT 操作 ==========================

    def _alloc_block(self) -> int:
        """分配一个空闲数据块，返回块号"""
        for i in range(DATA_START, TOTAL_BLOCKS):
            if not self.bitmap[i]:
                self._mark_used(i)
                self.fat[i] = FAT_EOF
                return i
        raise OSError("磁盘空间不足！")

    def _alloc_blocks(self, count: int) -> List[int]:
        """分配并链接 count 个块，返回块号列表"""
        if count <= 0:
            return []
        blocks = [self._alloc_block() for _ in range(count)]
        for i in range(len(blocks) - 1):
            self.fat[blocks[i]] = blocks[i + 1]
        if blocks:
            self.fat[blocks[-1]] = FAT_EOF
        return blocks

    def _free_chain(self, start_block: int) -> None:
        """释放从 start_block 开始的整个块链"""
        current = start_block
        visited: set = set()
        while current != FAT_EOF and current not in visited:
            visited.add(current)
            nxt = self.fat[current]
            self._mark_free(current)
            current = nxt

    def _get_chain(self, start_block: int) -> List[int]:
        """获取块链中所有块号"""
        blocks: List[int] = []
        current = start_block
        visited: set = set()
        while current != FAT_EOF and current not in visited:
            visited.add(current)
            blocks.append(current)
            current = self.fat[current]
        return blocks

    def _read_chain_data(self, first_block: int, size: int) -> bytes:
        """从块链读取 size 字节数据"""
        blocks = self._get_chain(first_block)
        data = bytearray()
        remaining = size
        for blk in blocks:
            if remaining <= 0:
                break
            chunk = self._read_block(blk)
            data.extend(chunk[:min(remaining, BLOCK_SIZE)])
            remaining -= min(remaining, BLOCK_SIZE)
        return bytes(data)

    def _write_chain_data(self, first_block: int, data: bytes, old_size: int) -> Tuple[int, int]:
        """将数据写入块链，返回 (new_first_block, new_size)"""
        new_size = len(data)
        old_blk_cnt = (old_size + BLOCK_SIZE - 1) // BLOCK_SIZE if old_size > 0 else 0
        new_blk_cnt = (new_size + BLOCK_SIZE - 1) // BLOCK_SIZE if new_size > 0 else 0

        # ---- 空文件 ----
        if new_blk_cnt == 0:
            self._free_chain(first_block)
            return FAT_EOF, 0

        # ---- 调整块链长度 ----
        if old_blk_cnt == new_blk_cnt:
            blocks = self._get_chain(first_block)
        elif old_blk_cnt < new_blk_cnt:
            blocks = self._get_chain(first_block)
            extra = self._alloc_blocks(new_blk_cnt - old_blk_cnt)
            if blocks:
                self.fat[blocks[-1]] = extra[0]
            else:
                blocks = extra
            blocks.extend(extra)
        else:  # old > new，释放多余块
            blocks = self._get_chain(first_block)
            for blk in blocks[new_blk_cnt:]:
                self._free_chain(blk)
            blocks = blocks[:new_blk_cnt]
            if blocks:
                self.fat[blocks[-1]] = FAT_EOF

        # ---- 写入数据 ----
        offset = 0
        for blk in blocks:
            if offset >= new_size:
                break
            chunk = data[offset:offset + BLOCK_SIZE]
            self._write_block(blk, chunk.ljust(BLOCK_SIZE, b'\x00'))
            offset += BLOCK_SIZE

        return (blocks[0] if blocks else FAT_EOF), new_size

    # ====================== 目录操作 ==========================

    def _read_dir_entries(self, dir_block: int) -> List[Tuple[int, int, DirEntry]]:
        """读取目录中的所有有效条目 → [(块号, 槽位, DirEntry), ...]"""
        entries: List[Tuple[int, int, DirEntry]] = []
        for blk in self._get_chain(dir_block):
            data = self._read_block(blk)
            for i in range(ENTRIES_PER_BLK):
                offset = i * DIR_ENTRY_SIZE
                entry_data = data[offset:offset + DIR_ENTRY_SIZE]
                if entry_data[0] == 0:          # 空槽
                    continue
                entry = DirEntry.unpack(entry_data)
                if entry.name and entry.name[0] != '\x00':
                    entries.append((blk, i, entry))
        return entries

    def _find_dir_entry(self, dir_block: int, name: str) -> Optional[Tuple[int, int, DirEntry]]:
        """在目录中查找指定名称的条目"""
        for blk in self._get_chain(dir_block):
            data = self._read_block(blk)
            for i in range(ENTRIES_PER_BLK):
                offset = i * DIR_ENTRY_SIZE
                entry_data = data[offset:offset + DIR_ENTRY_SIZE]
                if entry_data[0] == 0:
                    continue
                entry = DirEntry.unpack(entry_data)
                if entry.name == name:
                    return (blk, i, entry)
        return None

    def _add_dir_entry(self, dir_block: int, entry: DirEntry) -> None:
        """向目录中添加一个条目（自动扩容）"""
        blocks = self._get_chain(dir_block)

        # 先找空闲槽
        for blk in blocks:
            data = bytearray(self._read_block(blk))
            for i in range(ENTRIES_PER_BLK):
                offset = i * DIR_ENTRY_SIZE
                if data[offset] == 0:
                    data[offset:offset + DIR_ENTRY_SIZE] = entry.pack()
                    self._write_block(blk, bytes(data))
                    return

        # 无空槽 → 分配新块
        new_blk = self._alloc_block()
        self.fat[blocks[-1]] = new_blk
        self.fat[new_blk] = FAT_EOF
        self._clear_block(new_blk)
        data = bytearray(b'\x00' * BLOCK_SIZE)
        data[0:DIR_ENTRY_SIZE] = entry.pack()
        self._write_block(new_blk, bytes(data))

    def _remove_dir_entry(self, dir_block: int, name: str) -> bool:
        """从目录中移除条目（清空对应槽）"""
        result = self._find_dir_entry(dir_block, name)
        if not result:
            return False
        blk, idx, _ = result
        data = bytearray(self._read_block(blk))
        offset = idx * DIR_ENTRY_SIZE
        data[offset:offset + DIR_ENTRY_SIZE] = b'\x00' * DIR_ENTRY_SIZE
        self._write_block(blk, bytes(data))
        return True

    def _update_dir_entry(self, dir_block: int, name: str, entry: DirEntry) -> bool:
        """更新目录项"""
        result = self._find_dir_entry(dir_block, name)
        if not result:
            return False
        blk, idx, _ = result
        data = bytearray(self._read_block(blk))
        offset = idx * DIR_ENTRY_SIZE
        data[offset:offset + DIR_ENTRY_SIZE] = entry.pack()
        self._write_block(blk, bytes(data))
        return True

    # ====================== 路径解析 ==========================

    def _traverse(self, components: List[str]) -> int:
        """从根目录沿 components 逐级下钻，返回目标块号"""
        current = ROOT_START
        for comp in components:
            found = self._find_dir_entry(current, comp)
            if not found:
                raise FileNotFoundError(f"路径不存在: /{'/'.join(components)}")
            current = found[2].first_block
        return current

    def _resolve_path(self, path: str) -> Tuple[List[str], int]:
        """
        解析路径 → (路径分量列表, 目标块号)
        支持 .  ..  /  相对/绝对路径
        """
        path = path.strip()
        if not path or path == '.':
            return self.current_path.copy(), self.current_block
        if path == '..':
            if not self.current_path:
                return [], ROOT_START
            new_path = self.current_path[:-1]
            return new_path, self._traverse(new_path) if new_path else ROOT_START
        if path == '/':
            return [], ROOT_START

        # 拆分分量
        absolute = path.startswith('/')
        raw = [c for c in path.split('/') if c and c != '.']

        if absolute:
            current_path: List[str] = []
            current_block = ROOT_START
        else:
            current_path = self.current_path.copy()
            current_block = self.current_block

        for comp in raw:
            if comp == '..':
                if current_path:
                    current_path.pop()
                    current_block = self._traverse(current_path) if current_path else ROOT_START
                continue
            found = self._find_dir_entry(current_block, comp)
            if not found:
                raise FileNotFoundError(f"路径不存在: {path}")
            entry = found[2]
            if not entry.is_dir:
                raise NotADirectoryError(f"不是目录: {comp}")
            current_block = entry.first_block
            current_path.append(comp)

        return current_path, current_block

    @staticmethod
    def _path_str(components: List[str]) -> str:
        return '/' + '/'.join(components) if components else '/'

    def pwd(self) -> str:
        return self._path_str(self.current_path)

    # ---- 快捷：找父目录 & 项目名 -----------------------------
    def _split_path(self, path: str) -> Tuple[str, str]:
        """返回 (父路径, 项目名)"""
        path = path.rstrip('/')
        if not path or path == '/':
            raise ValueError("路径不能为根目录")
        if '/' not in path:
            return '.', path
        parts = path.rsplit('/', 1)
        parent = parts[0] if parts[0] else '/'
        return parent, parts[1]

    def _resolve_entry(self, path: str) -> Tuple[int, DirEntry]:
        """解析到某个存在的条目 → (父目录块号, 目标DirEntry)"""
        parent_path, name = self._split_path(path)
        _, parent_block = self._resolve_path(parent_path)
        found = self._find_dir_entry(parent_block, name)
        if not found:
            raise FileNotFoundError(f"不存在: {path}")
        return parent_block, found[2]

    # ====================== 文件操作 ==========================

    def create_file(self, path: str, size: int = 0) -> DirEntry:
        parent_path, name = self._split_path(path)
        if not name or len(name) >= NAME_MAX:
            raise ValueError(f"文件名无效或过长（最大{NAME_MAX-1}字符）")

        _, parent_block = self._resolve_path(parent_path)
        if self._find_dir_entry(parent_block, name):
            raise FileExistsError(f"文件已存在: {name}")

        now = time.time()
        entry = DirEntry(name=name, attr=ATTR_FILE, first_block=FAT_EOF,
                         size=0, create_time=now, modify_time=now)

        if size > 0:
            entry.first_block, entry.size = self._write_chain_data(FAT_EOF, b'\x00' * size, 0)

        self._add_dir_entry(parent_block, entry)
        return entry

    def delete_file(self, path: str) -> None:
        parent_block, entry = self._resolve_entry(path)
        if entry.is_dir:
            raise IsADirectoryError(f"是目录而非文件: {path}")
        self._free_chain(entry.first_block)
        _, name = self._split_path(path)
        self._remove_dir_entry(parent_block, name)

    def open_file(self, path: str, mode: str = 'r') -> OpenFile:
        if path in self.open_files:
            raise OSError(f"文件已打开: {path}")
        _, entry = self._resolve_entry(path)
        if entry.is_dir:
            raise IsADirectoryError(f"是目录: {path}")
        of = OpenFile(path=path, entry=entry, offset=0, mode=mode)
        self.open_files[path] = of
        return of

    def close_file(self, path: str) -> None:
        if path not in self.open_files:
            raise OSError(f"文件未打开: {path}")
        del self.open_files[path]

    def write_file(self, path: str, data: bytes, offset: Optional[int] = None) -> int:
        parent_block, entry = self._resolve_entry(path)
        if entry.is_dir:
            raise IsADirectoryError(f"是目录: {path}")

        old = b''
        if entry.size > 0:
            old = self._read_chain_data(entry.first_block, entry.size)

        if offset is None:
            offset = len(old)

        if offset > len(old):
            old = old.ljust(offset, b'\x00')

        new_data = old[:offset] + data + old[offset + len(data):]
        entry.first_block, entry.size = self._write_chain_data(entry.first_block, new_data, entry.size)
        entry.modify_time = time.time()
        self._update_dir_entry(parent_block, entry.name, entry)
        return len(data)

    def read_file(self, path: str, offset: int = 0, length: Optional[int] = None) -> bytes:
        _, entry = self._resolve_entry(path)
        if entry.is_dir:
            raise IsADirectoryError(f"是目录: {path}")
        if entry.size == 0:
            return b''
        data = self._read_chain_data(entry.first_block, entry.size)
        if offset >= len(data):
            return b''
        end = offset + length if length is not None else len(data)
        return data[offset:end]

    def stat_file(self, path: str) -> DirEntry:
        _, entry = self._resolve_entry(path)
        return entry

    # ====================== 目录操作 ==========================

    def make_dir(self, path: str) -> DirEntry:
        parent_path, name = self._split_path(path)
        if not name or len(name) >= NAME_MAX:
            raise ValueError(f"目录名无效或过长（最大{NAME_MAX-1}字符）")

        _, parent_block = self._resolve_path(parent_path)
        if self._find_dir_entry(parent_block, name):
            raise FileExistsError(f"已存在: {name}")

        now = time.time()
        dir_blk = self._alloc_block()
        self._clear_block(dir_blk)

        entry = DirEntry(name=name, attr=ATTR_DIR, first_block=dir_blk,
                         size=0, create_time=now, modify_time=now)

        # 自引用 "." 和 父引用 ".."
        self._add_dir_entry(dir_blk, DirEntry('.', ATTR_DIR, dir_blk, 0, now, now))
        self._add_dir_entry(dir_blk, DirEntry('..', ATTR_DIR, parent_block, 0, now, now))

        self._add_dir_entry(parent_block, entry)
        return entry

    def remove_dir(self, path: str) -> None:
        parent_block, entry = self._resolve_entry(path)
        if not entry.is_dir:
            raise NotADirectoryError(f"不是目录: {path}")

        # 检查空目录（仅含 . 和 ..）
        children = [e for _, _, e in self._read_dir_entries(entry.first_block)
                    if e.name not in ('.', '..')]
        if children:
            raise OSError(f"目录非空，无法删除: {path}")

        self._free_chain(entry.first_block)
        _, name = self._split_path(path)
        self._remove_dir_entry(parent_block, name)

    def list_dir(self, path: str = '.') -> List[DirEntry]:
        _, dir_block = self._resolve_path(path)
        return [e for _, _, e in self._read_dir_entries(dir_block)
                if e.name not in ('.', '..')]

    def change_dir(self, path: str) -> str:
        components, block = self._resolve_path(path)
        self.current_path = components
        self.current_block = block
        return self.pwd()

    # ====================== 扩展功能 ==========================

    def copy_file(self, src: str, dst: str) -> None:
        """复制文件"""
        data = self.read_file(src)
        self.create_file(dst, len(data))
        self.write_file(dst, data, offset=0)

    def move_file(self, src: str, dst: str) -> None:
        """移动 / 重命名"""
        src_parent, src_name = self._split_path(src)
        dst_parent_path, dst_name = self._split_path(dst)

        src_pb, src_entry = self._resolve_entry(src)
        _, dst_pb = self._resolve_path(dst_parent_path)

        if self._find_dir_entry(dst_pb, dst_name):
            raise FileExistsError(f"目标已存在: {dst_name}")

        # 在目标目录创建新条目（共享同一块链）
        now = time.time()
        new_entry = DirEntry(name=dst_name, attr=src_entry.attr,
                             first_block=src_entry.first_block,
                             size=src_entry.size,
                             create_time=src_entry.create_time,
                             modify_time=now)
        self._add_dir_entry(dst_pb, new_entry)

        # 从源目录移除
        self._remove_dir_entry(src_pb, src_name)

    def search_files(self, pattern: str, dir_block: Optional[int] = None,
                     base: str = '') -> List[str]:
        """递归搜索匹配 pattern 的文件/目录"""
        if dir_block is None:
            dir_block = ROOT_START
            base = '/'

        results: List[str] = []
        for _, _, e in self._read_dir_entries(dir_block):
            if e.name in ('.', '..'):
                continue
            full = base + e.name
            if pattern.lower() in e.name.lower():
                tag = '[目录]' if e.is_dir else '[文件]'
                sz = f" ({self._fmt_size(e.size)})" if e.is_file else ''
                results.append(f"{tag} {full}{sz}")
            if e.is_dir:
                results.extend(self.search_files(pattern, e.first_block, full + '/'))
        return results

    def get_tree(self, block: Optional[int] = None, name: str = '/') -> dict:
        """递归构建目录树（供 GUI 使用）"""
        if block is None:
            block = ROOT_START
        node: dict = {'name': name, 'type': 'dir', 'children': []}
        for _, _, e in self._read_dir_entries(block):
            if e.name in ('.', '..'):
                continue
            if e.is_dir:
                node['children'].append(self.get_tree(e.first_block, e.name))
            else:
                node['children'].append({
                    'name': e.name, 'type': 'file',
                    'size': e.size, 'modify_time': e.modify_time
                })
        return node

    def get_dir_details(self, path: str = '.') -> List[dict]:
        """获取目录内容（供 GUI 表格使用）"""
        _, dir_block = self._resolve_path(path)
        result: List[dict] = []
        for _, _, e in self._read_dir_entries(dir_block):
            if e.name in ('.', '..'):
                continue
            result.append({
                'name': e.name,
                'type': 'dir' if e.is_dir else 'file',
                'size': e.size,
                'size_str': self._fmt_size(e.size) if e.is_file else '-',
                'create_time': datetime.fromtimestamp(e.create_time).strftime('%Y-%m-%d %H:%M:%S'),
                'modify_time': datetime.fromtimestamp(e.modify_time).strftime('%Y-%m-%d %H:%M:%S'),
                'first_block': e.first_block,
            })
        # 目录在前，文件在后；各自按名称排序
        result.sort(key=lambda x: (0 if x['type'] == 'dir' else 1, x['name'].lower()))
        return result

    def disk_usage(self) -> Tuple[int, int, int]:
        """返回 (总容量, 已用, 空闲) 字节数"""
        total = TOTAL_BLOCKS * BLOCK_SIZE
        used = sum(1 for b in self.bitmap if b) * BLOCK_SIZE
        return total, used, total - used

    @staticmethod
    def _fmt_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        elif size < 1024 ** 2:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 ** 3:
            return f"{size / (1024**2):.1f} MB"
        return f"{size / (1024**3):.1f} GB"

    # ====================== 持久化 ==========================

    def save(self, filename: str = "filesystem.img") -> None:
        """保存文件系统到磁盘（原子写入 + 自动备份）"""
        self._write_super_block()
        # 先写到临时文件，成功后再原子替换，防止保存中断导致损坏
        tmp = filename + '.tmp'
        try:
            with open(tmp, 'wb') as f:
                f.write(self.storage)
                f.write(struct.pack(f'<{TOTAL_BLOCKS}i', *self.fat))
                f.write(bytes([1 if b else 0 for b in self.bitmap]))
                path_bytes = '/'.join(self.current_path).encode('utf-8')
                f.write(struct.pack('<I', len(path_bytes)))
                f.write(path_bytes)
                f.flush()
                os.fsync(f.fileno())
            # 保留旧文件作为 .bak，再替换
            if os.path.exists(filename):
                try:
                    os.replace(filename, filename + '.bak')
                except OSError:
                    pass  # 备份失败不阻塞保存
            os.replace(tmp, filename)
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            raise

    def load(self, filename: str = "filesystem.img") -> bool:
        """从磁盘加载文件系统（含完整性校验）"""
        if not os.path.exists(filename):
            return False

        EXPECTED_SIZE = (BLOCK_SIZE * TOTAL_BLOCKS
                         + TOTAL_BLOCKS * 4     # FAT
                         + TOTAL_BLOCKS          # bitmap
                         + 4)                    # path_len (minimum)
        actual_size = os.path.getsize(filename)
        if actual_size < EXPECTED_SIZE:
            raise OSError(
                f'磁盘映像文件异常（{actual_size} 字节 < 预期最低 {EXPECTED_SIZE} 字节），'
                f'文件可能已损坏。将自动格式化新文件系统。'
            )

        with open(filename, 'rb') as f:
            # — 存储区 —
            storage_data = f.read(BLOCK_SIZE * TOTAL_BLOCKS)
            if len(storage_data) < BLOCK_SIZE * TOTAL_BLOCKS:
                raise OSError('磁盘映像截断：存储区不完整')
            self.storage = bytearray(storage_data)

            # — FAT 表 —
            fat_raw = f.read(TOTAL_BLOCKS * 4)
            if len(fat_raw) < TOTAL_BLOCKS * 4:
                raise OSError('磁盘映像截断：FAT 表不完整')
            self.fat = list(struct.unpack(f'<{TOTAL_BLOCKS}i', fat_raw))

            # — 位图 —
            bitmap_raw = f.read(TOTAL_BLOCKS)
            if len(bitmap_raw) < TOTAL_BLOCKS:
                raise OSError('磁盘映像截断：位图不完整')
            self.bitmap = [b == 1 for b in bitmap_raw]

            # — 当前路径 —
            plen_data = f.read(4)
            if plen_data and len(plen_data) == 4:
                plen = struct.unpack('<I', plen_data)[0]
                path_bytes = f.read(plen)
                if len(path_bytes) == plen:
                    path_str = path_bytes.decode('utf-8', errors='replace')
                    self.current_path = [c for c in path_str.split('/') if c]
                else:
                    self.current_path = []
            else:
                self.current_path = []

        # — 魔数校验 —
        if not self._read_super_block():
            # 尝试从备份恢复
            bak = filename + '.bak'
            if os.path.exists(bak):
                if self.load(bak):
                    # 恢复成功，把备份还原为主文件
                    try:
                        os.replace(bak, filename)
                    except OSError:
                        pass
                    return True
            raise OSError(
                '磁盘映像魔数校验失败 —— 文件格式不匹配或数据已损坏。'
                '将自动格式化新文件系统。'
            )

        # — 恢复当前目录 —
        try:
            self.current_block = self._traverse(self.current_path) if self.current_path else ROOT_START
        except Exception:
            self.current_path = []
            self.current_block = ROOT_START

        self._initialized = True
        return True
