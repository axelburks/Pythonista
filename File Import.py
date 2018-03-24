import os, ui, re, appex, console, shutil, time, threading, functools 
from objc_util import ObjCInstance, ObjCClass
from operator import attrgetter

def human_size(size_bytes):
	'''Helper function for formatting human-readable file sizes'''
	if size_bytes == 1:
		return "1 byte"
	suffixes_table = [('bytes',0),('KB',0),('MB',1),('GB',2),('TB',2), ('PB',2)]
	num = float(size_bytes)
	for suffix, precision in suffixes_table:
		if num < 1024.0:
			break
		num /= 1024.0
	if precision == 0:
		formatted_size = "%d" % num
	else:
		formatted_size = str(round(num, ndigits=precision))
	return "%s %s" % (formatted_size, suffix)

class TreeNode (object):
	def __init__(self):
		self.expanded = False
		self.children = None
		self.leaf = True
		self.title = ''
		self.subtitle = ''
		self.icon_name = None
		self.level = 1
		self.enabled = True
		self.subnode = True

	def expand_children(self):
		self.expanded = True
		self.children = []

	def collapse_children(self):
		self.expanded = False

	def __repr__(self):
		return '<TreeNode: "%s"%s>' % (self.title, ' (expanded)' if self.expanded else '')

class FileTreeNode (TreeNode):
	def __init__(self, path, show_size=True, select_dirs=True,   
               file_pattern=None):
		TreeNode.__init__(self)
		self.path = path
		self.title = os.path.split(path)[1]
		self.select_dirs = select_dirs
		self.file_pattern = file_pattern
		is_dir = os.path.isdir(path)
		self.leaf = not is_dir
		ext = os.path.splitext(path)[1].lower()
		if is_dir:
			self.icon_name = 'Folder'
		elif ext == '.py':
			self.icon_name = 'FilePY'
		elif ext == '.pyui':
			self.icon_name = 'FileUI'
		elif ext in ('.png', '.jpg', '.jpeg', '.gif'):
			self.icon_name = 'FileImage'
		else:
			self.icon_name = 'FileOther'
		self.show_size = show_size
		if not is_dir and show_size:
			self.subtitle = human_size((os.stat(self.path).st_size))
		if is_dir and not select_dirs:
			self.enabled = False
		elif not is_dir:
			filename = os.path.split(path)[1]
			self.enabled = not file_pattern or re.match(file_pattern, filename)

	@property
	def cmp_title(self):
		return self.title.lower()

	def expand_children(self):
		if self.children is not None:
			self.expanded = True
			return
		files = os.listdir(self.path)
		children = []
		
		for filename in files:
			if filename.startswith('.'):
				continue
			full_path = os.path.join(self.path, filename)
			node = FileTreeNode(full_path, self.show_size, self.select_dirs, self.file_pattern)
			node.level = self.level + 1
			children.append(node)
		self.expanded = True
		self.children = sorted(children, key=attrgetter('subnode', 'leaf', 'cmp_title'))

class TreeDialogController (object):
	def __init__(self, root_node, allow_multi=False, async_mode=False):
		self.async_mode = async_mode
		self.allow_multi = allow_multi
		self.selected_entries = None
		self.table_view = ui.TableView()
		self.table_view.frame = (0, 0, 500, 500)
		self.table_view.data_source = self
		self.table_view.delegate = self
		self.table_view.flex = 'WH'
		self.table_view.allows_multiple_selection = allow_multi
		self.table_view.tint_color = 'gray'
		self.view = ui.View(frame=self.table_view.frame)
		self.view.add_subview(self.table_view)
		self.view.name = '请选择存储位置'
		self.busy_view = ui.View(frame=self.view.bounds, flex='WH', background_color=(0, 0, 0, 0.35))
		hud = ui.View(frame=(self.view.center.x - 50, self.view.center.y - 50, 100, 100))
		hud.background_color = (0, 0, 0, 0.7)
		hud.corner_radius = 8.0
		hud.flex = 'TLRB'
		spinner = ui.ActivityIndicator()
		spinner.style = ui.ACTIVITY_INDICATOR_STYLE_WHITE_LARGE
		spinner.center = (50, 50)
		spinner.start_animating()
		hud.add_subview(spinner)
		self.busy_view.add_subview(hud)
		self.busy_view.alpha = 0.0
		self.view.add_subview(self.busy_view)
		self.done_btn = ui.ButtonItem(title='Done', action=self.done_action)
		self.view.right_button_items = [self.done_btn]
		self.done_btn.enabled = False
		self.root_node = root_node
		self.entries = []
		self.flat_entries = []
		if self.async_mode:
			self.set_busy(True)
			t = threading.Thread(target=self.expand_root)
			t.start()
		else:
			self.expand_root()

	def expand_root(self):
		tree = []
		self.root_node.level = 1
		tree.append(self.root_node)
		self.root_node.expand_children()
		self.set_busy(False)
		self.entries = tree + self.root_node.children
		self.flat_entries = self.entries
		self.table_view.reload()
	
	def flatten_entries(self, entries, dest=None):
		if dest is None:
			dest = []
		for entry in entries:
			dest.append(entry)
			if not entry.leaf and entry.expanded:
				self.flatten_entries(entry.children, dest)
		return dest
		
	def rebuild_flat_entries(self):
		self.flat_entries = self.flatten_entries(self.entries)

	def tableview_number_of_rows(self, tv, section):
		return len(self.flat_entries)

	def tableview_cell_for_row(self, tv, section, row):
		cell = ui.TableViewCell()
		entry = self.flat_entries[row]
		level = entry.level - 1
		image_view = ui.ImageView(frame=(44 + 20*level, 5, 34, 34))
		label_x = 44+34+8+20*level
		label_w = cell.content_view.bounds.w - label_x - 8
		if entry.subtitle:
			label_frame = (label_x, 0, label_w, 26)
			sub_label = ui.Label(frame=(label_x, 26, label_w, 14))
			sub_label.font = ('<System>', 12)
			sub_label.text = entry.subtitle
			sub_label.text_color = '#999'
			cell.content_view.add_subview(sub_label)
		else:
			label_frame = (label_x, 0, label_w, 44)
		label = ui.Label(frame=label_frame)
		if entry.subtitle:
			label.font = ('<System>', 15)
		else:
			label.font = ('<System>', 18)
		label.text = entry.title
		label.flex = 'W'
		cell.content_view.add_subview(label)
		if entry.leaf and not entry.enabled:
			label.text_color = '#999'
		cell.content_view.add_subview(image_view)
		if not entry.leaf:
			has_children = entry.expanded
			btn = ui.Button(image=ui.Image.named('CollapseFolder' if has_children else 'ExpandFolder'))
			btn.frame = (20*level, 0, 44, 44)
			btn.action = self.expand_dir_action
			cell.content_view.add_subview(btn)
		if entry.icon_name:
			image_view.image = ui.Image.named(entry.icon_name)
		else:
			image_view.image = None
		cell.selectable = entry.enabled
		return cell

	def row_for_view(self, sender):
		'''Helper to find the row index for an 'expand' button'''
		cell = ObjCInstance(sender)
		while not cell.isKindOfClass_(ObjCClass('UITableViewCell')):
			cell = cell.superview()
		return ObjCInstance(self.table_view).indexPathForCell_(cell).row()

	def expand_dir_action(self, sender):
		'''Invoked by 'expand' button'''
		row = self.row_for_view(sender)
		entry = self.flat_entries[row]
		if entry.expanded:
			sender.image = ui.Image.named('ExpandFolder')
		else:
			sender.image = ui.Image.named('CollapseFolder')
		self.toggle_dir(row)
		self.update_done_btn()

	def toggle_dir(self, row):
		'''Expand or collapse a folder node'''
		entry = self.flat_entries[row]
		if entry.expanded:
			entry.collapse_children()
			old_len = len(self.flat_entries)
			self.rebuild_flat_entries()
			num_deleted = old_len - len(self.flat_entries)
			deleted_rows = range(row + 1, row + num_deleted + 1)
			self.table_view.delete_rows(deleted_rows)
		else:
			if self.async_mode:
				self.set_busy(True)
				expand = functools.partial(self.do_expand, entry, row)
				t = threading.Thread(target=expand)
				t.start()
			else:
				self.do_expand(entry, row)

	def do_expand(self, entry, row):
		'''Actual folder expansion (called on background thread if async_mode is enabled)'''
		entry.expand_children()
		self.set_busy(False)
		old_len = len(self.flat_entries)
		self.rebuild_flat_entries()
		num_inserted = len(self.flat_entries) - old_len
		inserted_rows = range(row + 1, row + num_inserted + 1)
		self.table_view.insert_rows(inserted_rows)

	def tableview_did_select(self, tv, section, row):
		self.update_done_btn()

	def tableview_did_deselect(self, tv, section, row):
		self.update_done_btn()

	def update_done_btn(self):
		'''Deactivate the done button when nothing is selected'''
		selected = [self.flat_entries[i[1]] for i in self.table_view.selected_rows if self.flat_entries[i[1]].enabled]
		self.done_btn.enabled = len(selected) > 0

	def set_busy(self, flag):
		'''Show/hide spinner overlay'''
		def anim():
			self.busy_view.alpha = 1.0 if flag else 0.0
		ui.animate(anim)

	def done_action(self, sender):
		self.selected_entries = [self.flat_entries[i[1]] for i in self.table_view.selected_rows if self.flat_entries[i[1]].enabled]
		self.view.close()

def file_picker_dialog(title=None, root_dir=None, multiple=False,
                       select_dirs=False, file_pattern=None, show_size=True):
	if root_dir is None:
		root_dir = os.path.expanduser('~')
	if title is None:
		title = os.path.split(root_dir)[1]
	root_node = FileTreeNode(root_dir, show_size, select_dirs, file_pattern)
	root_node.title = title or ''
	picker = TreeDialogController(root_node, allow_multi=multiple, async_mode=True)
	picker.view.present('sheet')
	picker.view.wait_modal()
	if picker.selected_entries is None:
		return None
	paths = [e.path for e in picker.selected_entries]
	if multiple:
		return paths
	else:
		return paths[0]

def file_save(get_path, dstpath):
	try:
		shutil.copy(get_path, dstpath)
		console.hud_alert('导入成功！','',1)
		appex.finish()
		exit()
	except Exception as eer:
		print(eer)
		console.hud_alert('导入失败！','error',1)

def file_import(get_path):
	file_name = os.path.basename(get_path)
	file_pure_name = os.path.splitext(file_name)[0]
	file_ext = os.path.splitext(file_name)[-1]
	file_loc = file_picker_dialog(None, root_dir=os.path.expanduser('~/Documents'), multiple=False, select_dirs=True, file_pattern=r'^.*\%s' % file_ext)

	if file_loc is None:
		appex.finish()
		exit()
	elif re.match(r'^.*\.\w+$', file_loc):
		file_save(get_path, file_loc)
	else:
		new_file_name = console.input_alert('文件名','文件格式: ' + file_ext,file_pure_name,'确认', hide_cancel_button=True)
		dstpath = os.path.join(file_loc, new_file_name + file_ext)
		while(os.path.exists(dstpath)):
			try:
				result = console.alert('文件名已存在',new_file_name + file_ext,'重命名','覆盖', hide_cancel_button=False)
				if result == 1:
					new_file_name = console.input_alert('重命名',new_file_name + file_ext,new_file_name,'确认', hide_cancel_button=True)
					dstpath = os.path.join(file_loc, new_file_name + file_ext)
					if not os.path.exists(dstpath):
						break
				if result == 2:
					break
			except:
				appex.finish()
				exit()
		file_save(get_path, dstpath)

def main():
	if appex.is_running_extension():
		if appex.get_file_path():
			get_path = appex.get_file_path()
			file_import(get_path)
		else:
			console.hud_alert('非文件无法导入', 'error', 2)
			appex.finish()
			exit()
	else:
		console.hud_alert('请在分享扩展中打开本脚本','error',2)
		exit()

if __name__ == '__main__':
	main()
