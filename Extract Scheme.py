import re, zipfile, plistlib, appex, console, dialogs, clipboard

def extract_plist_data(zip_path):
	try:
		myzip = zipfile.ZipFile(zip_path)
		plist_root = None
		for filename in myzip.namelist():
			if re.match(r'.+\.app\/Info\.plist',filename):
				plist = myzip.read(myzip.getinfo(filename))
				plist_root = plistlib.loads(plist)
		myzip.close()
		if plist_root is None:
			return None
		else:
			return plist_root
	except Exception as eer:
		console.hud_alert(str(eer),'error',1)
		exit()

def copy_scheme(plist):
	try:
		schemes = []
		for i in plist['CFBundleURLTypes']:
			schemes.append(i['CFBundleURLSchemes'][0])
		return schemes
	except:
		return None

def main():
	get_path = None
	if appex.is_running_extension() and appex.get_file_path():
		get_path = appex.get_file_path()
	else:
		console.hud_alert('No file input','error',1)
		exit()
		
	plist = extract_plist_data(get_path)
	if plist is None:
		console.hud_alert('No Info.plist file','error',1)
		exit()
	else:
		url_schemes = copy_scheme(plist)
		if url_schemes:
			result = dialogs.list_dialog('Select to Clips', url_schemes)
			if result:
				clipboard.set(result + '://')
				appex.finish()
				exit()
			else:
				exit()
		else:
			console.hud_alert('No Url Schemes','error',1)
			exit()
			
if __name__ == '__main__':
	main()
		
