import appex, console, shutil
from os import path

# 文件保存路径
save_dir = path.expanduser('~/Documents')

def simple_import():

	if appex.is_running_extension():
		if appex.get_file_path():
			get_path = appex.get_file_path()
			file_name = path.basename(get_path)
			file_pure_name = path.splitext(file_name)[0]
			file_ext = path.splitext(file_name)[-1]

			new_file_name = console.input_alert('文件名','文件格式：' + file_ext,file_pure_name,'确认', hide_cancel_button=True)
			dstpath = path.join(save_dir, new_file_name + file_ext)

			while(path.exists(dstpath)):
				try:
					result = console.alert('文件名已存在',new_file_name + file_ext,'重命名','覆盖', hide_cancel_button=False)
					if result == 1:
						new_file_name = console.input_alert('重命名',new_file_name + file_ext,new_file_name,'确认', hide_cancel_button=True)
						dstpath = path.join(save_dir, new_file_name + file_ext)
						if not path.exists(dstpath):
							break
					if result == 2:
						break

				except:
					appex.finish()
					exit()
			
			try:
				shutil.copy(get_path, dstpath)
				console.hud_alert('导入成功！','',1)
				appex.finish()
				exit()
			except Exception as eer:
				print(eer)
				console.hud_alert('导入失败！','error',1)
		else:
			console.hud_alert('非文件无法导入', 'error', 2)
			appex.finish()
			exit()
	else:
		console.hud_alert('请在分享扩展中打开本脚本','error',2)
		exit()

if __name__ == '__main__':
	simple_import()
