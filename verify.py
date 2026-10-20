# -*- coding: utf-8 -*-
"""端到端功能验证：跑一遍核心 API，打印每一步的真实结果。"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fs_core import FileSystem

OK = 0
FAIL = 0


def check(name, cond, extra=''):
    global OK, FAIL
    if cond:
        OK += 1
        print(f'  [PASS] {name}')
    else:
        FAIL += 1
        print(f'  [FAIL] {name} {extra}')


fs = FileSystem()
fs.format()
print('[1] 格式化')
total, used, free = fs.disk_usage()
print(f'    总容量 {total} B / 已用 {used} B / 空闲 {free} B')
check('总容量 = 1 MB', total == 1024 * 1024, total)

print('[2] 多级目录')
fs.make_dir('/home')
fs.make_dir('/home/docs')
fs.make_dir('/home/docs/deep')
fs.change_dir('/home/docs/deep')
check('pwd 正确', fs.pwd() == '/home/docs/deep', fs.pwd())
fs.change_dir('/')

print('[3] 目录自动扩容（单块只能放 6 条）')
for i in range(20):
    fs.create_file(f'/home/docs/f{i:02d}.txt', 0)
entries = fs.list_dir('/home/docs')
print(f'    /home/docs 下条目数 = {len(entries)}')
check('目录超过 6 条后自动扩容（20 文件 + 1 子目录）', len(entries) == 21, len(entries))

print('[4] 写入 / 读取（跨块文件）')
payload = bytes(range(256)) * 20  # 5120 字节 = 5 块
fs.create_file('/home/big.bin', 0)
n = fs.write_file('/home/big.bin', payload)
back = fs.read_file('/home/big.bin')
check('写入字节数 = 5120', n == 5120, n)
check('读回内容与写入一致', back == payload, f'{len(back)} bytes')
check('跨块后大小正确', fs.stat_file('/home/big.bin').size == 5120)

print('[5] 局部读写（offset / length）')
seg = fs.read_file('/home/big.bin', offset=1000, length=100)
check('局部读取正确', seg == payload[1000:1100], len(seg))
fs.write_file('/home/big.bin', b'HELLO', offset=2000)
back2 = fs.read_file('/home/big.bin')
check('定点覆写正确', back2[2000:2005] == b'HELLO' and len(back2) == 5120)

print('[6] 中文长文件名')
name = '操作系统课程设计说明文档.txt'
fs.create_file('/home/' + name, 0)
fs.write_file('/home/' + name, '中文内容测试'.encode('utf-8'))
check('中文名可创建并读回',
      fs.read_file('/home/' + name).decode('utf-8') == '中文内容测试')
check('中文名出现在列表中', any(e.name == name for e in fs.list_dir('/home')))

print('[7] 复制 / 移动 / 重命名')
fs.copy_file('/home/big.bin', '/home/big_copy.bin')
check('复制后内容一致', fs.read_file('/home/big_copy.bin') == back2)
fs.move_file('/home/big_copy.bin', '/home/docs/moved.bin')
check('移动后源不存在',
      not any(e.name == 'big_copy.bin' for e in fs.list_dir('/home')))
check('移动后目标存在',
      any(e.name == 'moved.bin' for e in fs.list_dir('/home/docs')))
fs.move_file('/home/docs/moved.bin', '/home/docs/renamed.bin')
check('同目录移动即重命名',
      any(e.name == 'renamed.bin' for e in fs.list_dir('/home/docs')))

print('[8] 搜索')
hits = fs.search_files('.txt')
print(f'    find .txt 命中 {len(hits)} 个')
check('子串搜索有结果', len(hits) >= 20, len(hits))

print('[9] 删除与空间回收')
before = fs.disk_usage()[1]
fs.delete_file('/home/big.bin')
after = fs.disk_usage()[1]
print(f'    删除前已用 {before} B → 删除后 {after} B')
check('删除 5KB 文件后释放 5120 B（5 块）', before - after == 5120, before - after)

print('[10] 删除非空目录应失败')
try:
    fs.remove_dir('/home')
    check('非空目录被拒绝删除', False, '竟然删成功了')
except OSError as e:
    check('非空目录被拒绝删除', True)
    print(f'    预期错误: {e}')

print('[11] 持久化往返')
img = os.path.join(tempfile.gettempdir(), '_fs_verify.img')
fs.save(img)
size = os.path.getsize(img)
expect = 1024 * 1024 + 1024 * 4 + 1024 + 4
print(f'    映像大小 = {size} 字节（1MB 存储区 + 4KB FAT + 1KB 位图 + 8B 头）')
check('映像大小符合布局', size == expect, f'{size} vs {expect}')
fs2 = FileSystem()
ok = fs2.load(img)
check('load 返回 True', ok)
check('重载后目录结构一致', len(fs2.list_dir('/home/docs')) == len(entries) + 1,
      len(fs2.list_dir('/home/docs')))
check('重载后中文文件仍在',
      any(e.name == name for e in fs2.list_dir('/home')))
fs2.change_dir('/home/docs')
check('重载后可继续 cd', fs2.pwd() == '/home/docs', fs2.pwd())
os.remove(img)

print('[12] 错误处理')
for path, exc in [('/nope/x.txt', FileNotFoundError),
                  ('/home', FileExistsError)]:
    try:
        fs.create_file(path, 0)
        check(f'create {path} 应抛错', False)
    except exc:
        check(f'create {path} 抛 {exc.__name__}', True)

print()
print(f'=== 结果: {OK} 通过 / {FAIL} 失败 ===')
sys.exit(1 if FAIL else 0)
