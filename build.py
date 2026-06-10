import PyInstaller.__main__
import os
import shutil

if __name__ == '__main__':
    # Clean previous builds
    for dir_name in ['build', 'dist_new']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name, ignore_errors=True)
            except Exception:
                pass

    # Prepare PyInstaller command
    PyInstaller.__main__.run([
        'main.py',
        '--name=SmartVMS',
        '--windowed',
        '--onedir',
        '--noconfirm',
        '--clean',
        '--distpath=dist_new',
        '--add-data=database/*.sql;database',
        '--add-data=assets;assets',
        '--add-data=web/templates;web/templates',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=bcrypt',
        '--hidden-import=flask',
        '--hidden-import=qrcode',
        '--hidden-import=PIL'
    ])
    
    # Copy vms.db and smtp_settings.json to the new build directory
    src_db_dir = os.path.join('database')
    dest_db_dir = os.path.join('dist_new', 'SmartVMS', 'database')
    
    if os.path.exists(src_db_dir) and os.path.exists(os.path.join('dist_new', 'SmartVMS')):
        os.makedirs(dest_db_dir, exist_ok=True)
        for filename in ['vms.db', 'smtp_settings.json']:
            src_file = os.path.join(src_db_dir, filename)
            dest_file = os.path.join(dest_db_dir, filename)
            if os.path.exists(src_file):
                try:
                    shutil.copy2(src_file, dest_file)
                    print(f"[SUCCESS] Copied {filename} to {dest_db_dir}")
                except Exception as e:
                    print(f"[WARNING] Failed to copy {filename}: {e}")
                    
        # Copy app_config.ini if it exists in root
        if os.path.exists('app_config.ini'):
            try:
                shutil.copy2('app_config.ini', os.path.join('dist_new', 'SmartVMS', 'app_config.ini'))
                print("[SUCCESS] Copied app_config.ini to dist_new/SmartVMS")
            except Exception as e:
                print(f"[WARNING] Failed to copy app_config.ini: {e}")

    print("\n[SUCCESS] Build complete! You can find the executable in the 'dist_new' folder.")
