import re, zipfile, plistlib, appex, console, dialogs, clipboard

def extract_plist_data(zip_path):
	try:
		myzip = zipfile.ZipFile(zip_path)
		plist_root = None
		plist_name = None
		for filename in myzip.namelist():
			if re.match(r'.+\.app\/Info\.plist',filename):
				if plist_name is None or len(filename) < len(plist_name):
					plist= myzip.read(myzip.getinfo(filename))
					plist_root = plistlib.loads(plist)
					plist_name = filename
		myzip.close()
		if plist_root is None:
			return None
		else:
			return plist_root
	except Exception as eer:
		console.hud_alert(str(eer),'error',1)
		exit()

def extract_scheme(plist):
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
		if not re.match(r'.+\.(ipa|zip)$',get_path):
			console.hud_alert('Not supported file types','error',1)
			appex.finish()
			exit()
	else:
		console.hud_alert('No file input','error',1)
		appex.finish()
		exit()
		
	plist = extract_plist_data(get_path)
	if plist is None:
		console.hud_alert('No Info.plist file','error',1)
		appex.finish()
		exit()
	else:
		url_schemes = extract_scheme(plist)
		if url_schemes:
			result = dialogs.list_dialog('Select to Clips', url_schemes)
			if result:
				clipboard.set(result + '://')
				console.hud_alert('Copied Success!','',1)
				appex.finish()
				exit()
			else:
				appex.finish()
				exit()
		else:
			console.hud_alert('No Url Schemes','error',1)
			appex.finish()
			exit()
			
if __name__ == '__main__':
	main()
		
