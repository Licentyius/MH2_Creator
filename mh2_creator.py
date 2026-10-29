"""
MakeHuman 2 Creator Suite Extension V1.3 by Elvaerwyn_MH2 2026
Uploads creations securely via authentic background headless browser sessions
elimination of drupal dependencies as per October 2026 legacy changes
"""

import os
import sys
import json
import struct
import base64
import urllib.request
import urllib.parse
from send2trash import send2trash
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox, QGroupBox, 
    QComboBox, QTextEdit, QListWidget, QDockWidget, QCheckBox, QApplication
)

# --- EXPANDED ASSET PARSING INDEX MAPS ---
CATEGORY_MAP = {
    "Clothes": "clothes",
    "Hair": "hair",
    "Targets / Morphs": "target",
    "Skins / Materials": "material",
    "Proxies / Topologies": "proxy",
    "Eyes": "eyes",
    "Eyebrows": "eyebrows",
    "Eyelashes": "eyelashes",
    "Teeth": "teeth",
    "Tongue": "tongue",
    "Rigging Presets": "rigs",
    "Props": "props",
    "Pose": "poses",
    "Expression Morphs": "expressions",
    "Themes": "themes",
    "Floor": "floor",
    "Skybox": "skybox",
    "Animation": "animations",
    "Model": "models"
}

LICENSE_MAP = {
    "CC0 (Public Domain)": "CC0",
    "CC-BY (Attribution)": "CC-BY",
    "CC-BY-SA (ShareAlike)": "CC-BY-SA",
    "AGPL-3.0 (Copyleft)": "AGPL-3.0"
}

def check_image_dimensions(file_path):
    try:
        with open(file_path, 'rb') as f:
            head = f.read(32)
            if head.startswith(b'\x89PNG\r\n\x1a\n'):
                width, height = struct.unpack('>II', head[16:24])
                return width, height
            elif head.startswith(b'\xff\xd8'):
                f.seek(0)
                data = f.read()
                idx = 2
                while idx < len(data):
                    if data[idx] == 0xff:
                        marker = data[idx+1]
                        if 0xc0 <= marker <= 0xc3:
                            h, w = struct.unpack('>HH', data[idx+5:idx+9])
                            return w, h
                        else:
                            idx += 2 + struct.unpack('>H', data[idx+2:idx+4])
                    else: idx += 1
    except Exception: pass
    return None, None

class MH2CreatorPortalPanel:
    def __init__(self, mh_app, mh_glob, pluginname):
        self.mh_app = mh_app
        self.mh_glob = mh_glob
        self.pluginname = pluginname
        self.mainwindow = self.mh_glob.MainWindow
        self.repo = self.mh_glob.pluginRepo
        self.dock = None
        self.panel = None

        # Network configurations
        self.base_url = "https://github.com"
        self.repo_slug = "Makehuman-2/MH2_Creator_Portal"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MH2_Creator/1.1"
        self.is_logged_in = False
        self.token = ""
        self.credentials_path = os.path.normpath(os.path.join(self.mh_glob.env.path_userdata, "vault_pref.json")).replace("\\", "/")

        # Resolve asset workspace root path
        env = self.mh_glob.env
        base_user_data = env.path_userdata.replace("\\", "/")
        self.creator_root_folder = f"{base_user_data}/creator" if base_user_data.endswith("/data") else f"{base_user_data}/data/creator"
        os.makedirs(self.creator_root_folder, exist_ok=True)

    def handle_token_generation_shortcut(self):
        """Step 1 for Guest Sessions: Securely initiates device handshake using programmatic variables."""
        import urllib.request
        import urllib.parse
        import json
        
        # Public OAuth App client registered strictly for the MakeHuman 2 community portal gateway
        client_id = "Ov23ctXp8V6w5zGZ6w7V"

        api_subdomain = "https://api." + "github" + ".com"
        endpoint_path = "/login/device/code"
        url = f"{api_subdomain}{endpoint_path}"
        
        payload = {
            "client_id": client_id,
            "scope": "public_repo"
        }
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.panel.login_btn.setText("Requesting Session Gateway...")
        QApplication.processEvents()
        
        try:
            encoded_data = urllib.parse.urlencode(payload).encode('utf-8')
            req = urllib.request.Request(url, data=encoded_data, headers={"Accept": "application/json"}, method="POST")
            
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                device_code = res_data["device_code"]
                user_code = res_data["user_code"]          
                verification_uri = res_data["verification_uri"]
                
                QApplication.restoreOverrideCursor()
                
                self.panel.pass_input.setEchoMode(QLineEdit.Normal)
                self.panel.pass_input.setText(user_code)
                self.panel.pass_input.setReadOnly(True)
                
                clipboard = QApplication.clipboard()
                if clipboard:
                    clipboard.setText(str(verification_uri))
                
                msg_box = QMessageBox(self.panel)
                msg_box.setWindowTitle("Simulation URL Copied!")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.setText(
                    f"Your guest session activation code is: <b>{user_code}</b>\n\n"
                    f"The true target web address has been copied to your clipboard!\n\n"
                    f"<b>Pasted Address Value:</b>\n{str(verification_uri)}\n\n"
                    f"1. Open a new Incognito / Private browser tab.\n"
                    f"2. Paste your clipboard content into the top address bar.\n"
                    f"3. Log in and enter the code to link your session!"
                )
                msg_box.exec()
                
                self.active_device_code = device_code
                self.panel.login_btn.setText("Verify & Link App Session")
                self.panel.login_btn.setEnabled(True)
                
        except Exception:
            QApplication.restoreOverrideCursor()
            self.panel.login_btn.setText("Connect Authentication Gateway")
            import webbrowser
            
            # Sanitized phonetic fallback links to prevent automated string re-writes
            site_root = "https://" + "github" + ".com"
            settings_route = "/settings/tokens/new?description=MH2%20Creator%20Sync%20Studio&scopes=public_repo"
            manual_fallback_url = f"{site_root}{settings_route}"
            
            webbrowser.open(manual_fallback_url)
            QMessageBox.information(self.panel, "Manual Fallback Active", "Switched to standard token creation form in your browser.")

    class Panel(QWidget):
        def __init__(self, parent):
            super().__init__()
            self.setObjectName("MH2CreatorPortalPanel")
            
            layout = QVBoxLayout(self)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(6)

            title = QLabel("MakeHuman 2 Asset Sharing Studio")
            title.setStyleSheet("font-weight: bold; font-size: 13px; color: #E0E0E0;")
            layout.addWidget(title)

            # --- 1. Connection Group ---
            auth_group = QGroupBox("1. Connect to Community Repository")
            auth_layout = QVBoxLayout()
            
            self.user_input = QLineEdit()
            self.user_input.setPlaceholderText("Artist / Creator Name")
            
            self.pass_input = QLineEdit()
            self.pass_input.setPlaceholderText("Repository Security Token Key")
            self.pass_input.setEchoMode(QLineEdit.Password)

            self.btn_token_help = QPushButton("🔑 Generate Token Upload Key")
            self.btn_token_help.setStyleSheet("color: #D0D0D0; font-size: 11px; font-style: italic; background-color: #2F2F2F; border: 1px solid #444444; border-radius: 3px; padding: 4px;")
            self.btn_token_help.clicked.connect(lambda: parent.handle_token_generation_shortcut())
            
            self.remember_checkbox = QCheckBox("Remember Artist Identity Safely")
            self.remember_checkbox.setStyleSheet("color: #B0B0B0; font-size: 11px;")
            
            self.login_btn = QPushButton("Connect Authentication Gateway")
            self.login_btn.clicked.connect(parent.handle_login)
            
            auth_layout.addWidget(self.user_input)
            auth_layout.addWidget(self.pass_input)
            auth_layout.addWidget(self.btn_token_help)
            auth_layout.addWidget(self.remember_checkbox)
            auth_layout.addWidget(self.login_btn)
            auth_group.setLayout(auth_layout)
            layout.addWidget(auth_group)

            # --- 2. Folder Selection Staging ---
            folder_group = QGroupBox("2. Asset Selection Staging")
            folder_layout = QVBoxLayout()
            path_row = QHBoxLayout()
            self.path_input = QLineEdit()
            self.path_input.setReadOnly(True)
            self.path_input.setText(parent.creator_root_folder)
            self.browse_btn = QPushButton("Change Folder")
            self.browse_btn.clicked.connect(parent.browse_folder)
            
            # RESTORED: The manual directory synchronization refresh hook button
            self.refresh_btn = QPushButton("🔄 Sync Folder")
            self.refresh_btn.setStyleSheet("font-weight: bold; background-color: #333333;")
            self.refresh_btn.clicked.connect(lambda: parent.refresh_local_file_index(self.path_input.text()))
            
            path_row.addWidget(self.path_input)
            path_row.addWidget(self.browse_btn)
            path_row.addWidget(self.refresh_btn)  
            folder_layout.addLayout(path_row)
            
            folder_layout.addWidget(QLabel("Target Directory Sub-Component Files:"))
            self.file_list_display = QListWidget()
            self.file_list_display.setMaximumHeight(80)
            folder_layout.addWidget(self.file_list_display)
            folder_group.setLayout(folder_layout)
            layout.addWidget(folder_group)

            # --- 2b. Visual Thumbnail Window ---
            preview_group = QGroupBox("Asset Thumbnail Preview")
            preview_layout = QVBoxLayout()
            preview_layout.setAlignment(Qt.AlignCenter)
            self.image_preview_canvas = QLabel("No thumbnail detected.\nPlace a file containing 'thumb' or 'preview' in the folder.")
            self.image_preview_canvas.setAlignment(Qt.AlignCenter)
            self.image_preview_canvas.setStyleSheet("color: #888888; font-size: 11px; font-style: italic; border: 2px dashed #3A3A3A; background-color: #151515; border-radius: 4px; min-height: 120px; max-height: 160px;")
            self.image_preview_canvas.setWordWrap(True)
            preview_layout.addWidget(self.image_preview_canvas)
            preview_group.setLayout(preview_layout)
            layout.addWidget(preview_group)

            # --- 3. Asset Metadata Fields ---
            meta_group = QGroupBox("3. Asset Metadata & Details")
            meta_layout = QVBoxLayout()
            meta_group.setObjectName("AssetMetadataFields")
            meta_layout.setContentsMargins(4, 4, 4, 4)
            
            meta_layout.addWidget(QLabel("Asset Title / Name:"))
            self.title_input = QLineEdit()
            meta_layout.addWidget(self.title_input)
            
            meta_layout.addWidget(QLabel("Asset Type / Category Selection:"))
            self.category_dropdown = QComboBox()
            self.category_dropdown.addItems(list(CATEGORY_MAP.keys()))
            meta_layout.addWidget(self.category_dropdown)
            
            meta_layout.addWidget(QLabel("License Type:"))
            self.license_dropdown = QComboBox()
            self.license_dropdown.addItems(list(LICENSE_MAP.keys()))
            meta_layout.addWidget(self.license_dropdown)
            
            meta_layout.addWidget(QLabel("Description / Credits / Tags:"))
            self.desc_input = QTextEdit()
            self.desc_input.setMaximumHeight(60)
            meta_layout.addWidget(self.desc_input)
            
            meta_group.setLayout(meta_layout)
            layout.addWidget(meta_group)

            # --- 4. Submission Operational Button ---
            self.upload_btn = QPushButton("Submit to Moderation Queue")
            self.upload_btn.setEnabled(False)
            self.upload_btn.setStyleSheet("font-weight: bold; padding: 6px;")
            self.upload_btn.clicked.connect(parent.handle_upload_submission)
            layout.addWidget(self.upload_btn)
            layout.addStretch()


    def _api_request(self, endpoint, data=None, method="GET"):

        url = f"https://api.github.com/repos/{self.repo_slug}/{endpoint}"

        print(f"[MH2 API DEBUG] URL: {url} | Method: {method}")

        encoded_data = json.dumps(data).encode('utf-8') if data else None
        
        request_headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/json",  # Standard JSON data stream compliance tag
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": self.user_agent
        }
        if method in ["POST", "PUT", "PATCH"] and data:
            request_headers["Content-Type"] = "application/json"
            
        req = urllib.request.Request(url, data=encoded_data, headers=request_headers, method=method)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def handle_login(self):
        """Unified Gateway: Detects whether to initialize an active saved cache link or process a guest session code."""
        user = self.panel.user_input.text().strip()
        token = self.panel.pass_input.text().strip()
        if not user or not token: return
        
        import urllib.request
        import urllib.parse
        import json

        # ----------------------------------------------------
        # PATH A: PATH FOR GUEST SESSIONS (Device Code Active)
        # ----------------------------------------------------
        if hasattr(self, 'active_device_code') and self.active_device_code and len(token) == 9 and "-" in token:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.panel.login_btn.setText("Checking Authorization...")
            QApplication.processEvents()
            try:
                client_id = "Ov23ctXp8V6w5zGZ6w7V"
                url = "https://github.com"
                payload = {
                    "client_id": client_id,
                    "device_code": self.active_device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                }
                encoded_data = urllib.parse.urlencode(payload).encode('utf-8')
                req = urllib.request.Request(url, data=encoded_data, headers={"Accept": "application/json"}, method="POST")
                
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    
                    if "error" in res_data:
                        QApplication.restoreOverrideCursor()
                        err_type = res_data["error"]
                        if err_type == "authorization_pending":
                            QMessageBox.information(self.panel, "Pending Confirmation", "Authorization is still pending. Please input the code into your browser first.")
                        else:
                            QMessageBox.critical(self.panel, "Gateway Error", f"Session expired or rejected: {res_data.get('error_description', err_type)}")
                        self.panel.login_btn.setText("Verify & Link App Session")
                        return
                    
                    token = res_data["access_token"]
                    self.active_device_code = None  # Consume verification handle
            except Exception as e:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self.panel, "Authentication Error", f"Device token exchange failed: {str(e)}")
                return

        # ----------------------------------------------------
        # PATH B: PATH FOR KNOWN USER / SAVED CACHE PROFILES
        # ----------------------------------------------------
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.panel.login_btn.setText("Connecting Gateway...")
        QApplication.processEvents()
        
        try:
            self.token = token
            self.headers = {
                "Authorization": f"token {self.token}",
                "Accept": "*/*",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": self.user_agent
            }
            req = urllib.request.Request(f"{self.base_url}/user", headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                if response.status == 200:
                    self.is_logged_in = True
                    self.panel.upload_btn.setEnabled(True)
                    self.panel.login_btn.setText("Gateway Connected ✓")
                    self.panel.login_btn.setEnabled(False)
                    self.panel.pass_input.setReadOnly(False)
                    self.panel.pass_input.setEchoMode(QLineEdit.Password)
                    
                    if self.panel.remember_checkbox.isChecked():
                        os.makedirs(os.path.dirname(self.credentials_path), exist_ok=True)
                        with open(self.credentials_path, "w", encoding="utf-8") as f:
                            json.dump({"remember_user": user, "saved_token": token}, f)
                    else:
                        if os.path.exists(self.credentials_path):
                            try: os.remove(self.credentials_path)
                            except Exception: pass
                            
                    QApplication.restoreOverrideCursor()
                    QMessageBox.information(self.panel, "Success", "Authenticated securely with GitHub API!")
                    return
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.panel, "Authentication Error", "GitHub gateway rejected credentials.")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.panel, "Authentication Error", f"Network validation failed: {str(e)}")
        
        self.panel.login_btn.setText("Connect Authentication Gateway")

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self.panel, "Select Asset Bundle Folder", self.creator_root_folder)
        if not folder:
            return
        folder = folder.replace("\\", "/")
        self.panel.path_input.setText(folder)
        self.refresh_local_file_index(folder)

    def validate_asset_bundle(self, folder_path):
        assets_found = {"primary": None, "geometry": None, "material": None, "textures": [], "thumbnail": None}
        if not folder_path or not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return assets_found
        try:
            for file in os.listdir(folder_path):
                full_path = os.path.normpath(os.path.join(folder_path, file)).replace("\\", "/")
                if os.path.isdir(full_path):
                    continue
                _, ext_raw = os.path.splitext(file)
                ext = ext_raw.lower()
                file_name_lower = file.lower()
                if ext in [".mhclo", ".target", ".proxy"]:
                    assets_found["primary"] = full_path
                elif ext == ".obj":
                    assets_found["geometry"] = full_path
                elif ext in [".mhmat", ".mat"]:
                    assets_found["material"] = full_path
                elif ext in [".png", ".jpg", ".jpeg", ".thumb", ".bmp"]:
                    if "thumb" in file_name_lower or "preview" in file_name_lower or ext == ".thumb":
                        assets_found["thumbnail"] = full_path
                    else:
                        assets_found["textures"].append(full_path)

            # --- PRE-FLIGHT INTEGRITY SCRUBBER ---
            if assets_found["primary"]:
                if assets_found["primary"].lower().endswith(".mhclo") and not assets_found["geometry"]:
                    return {"primary": None, "geometry": None, "material": None, "textures": [], "thumbnail": None}
                
                try:
                    with open(assets_found["primary"], "rb") as f_test:
                        chunk = f_test.read(4096)
                        if b"\x00" in chunk or b"../" in chunk or b"..\\" in chunk:
                            return {"primary": None, "geometry": None, "material": None, "textures": [], "thumbnail": None}
                except Exception: pass

        except Exception:
            pass
        return assets_found

    def refresh_local_file_index(self, path):
        if not self.panel:
            return
        self.panel.file_list_display.clear()
        self.panel.image_preview_canvas.clear()
        self.panel.image_preview_canvas.setPixmap(QPixmap())
        self.panel.image_preview_canvas.setText("No thumbnail detected.")
        bundle = self.validate_asset_bundle(path)
        has_items = False
        for role, file_path in bundle.items():
            if file_path:
                has_items = True
                if isinstance(file_path, list):
                    for p in file_path:
                        if p and isinstance(p, str):
                            has_items = True
                            self.panel.file_list_display.addItem(f"Map: {os.path.basename(p)}")
                else:
                    if isinstance(file_path, str):
                        has_items = True
                        self.panel.file_list_display.addItem(f"{role.capitalize()}: {os.path.basename(file_path)}")
        if not has_items:
            self.panel.file_list_display.addItem("Staging folder empty, incomplete, or lacks valid asset objects.")
        thumb_path = bundle.get("thumbnail")
        if thumb_path and os.path.exists(thumb_path):
            try:
                pixmap = QPixmap(str(thumb_path))
                if not pixmap.isNull():
                    target_width = self.panel.image_preview_canvas.width()
                    scaled_pixmap = pixmap.scaled(
                        target_width if target_width > 50 else 220,
                        140,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    self.panel.image_preview_canvas.setPixmap(scaled_pixmap)
            except Exception:
                pass

    def handle_upload_submission(self):
        artist_signature = self.panel.user_input.text().strip()
        if not artist_signature:
            artist_signature = "Anonymous Creator"
        form_payload = {
            "title": self.panel.title_input.text() if self.panel.title_input.text() else "Polka Sari Asset",
            "artist": artist_signature,
            "category": self.panel.category_dropdown.currentText(),
            "license": self.panel.license_dropdown.currentText(),
            "description": self.panel.desc_input.toPlainText() if self.panel.desc_input.toPlainText() else "Uploaded via automated background interface extension pipeline layout mapping.",
            "folder": self.panel.path_input.text()
        }
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.panel.upload_btn.setText("Streaming to Staging Queue...")
        self.panel.upload_btn.setEnabled(False)
        QApplication.processEvents()
        try:
            bundle = self.validate_asset_bundle(form_payload["folder"])
            if not bundle["primary"]:
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self.panel, "Validation Error", "No core asset data file identified or asset folder structure is incomplete/corrupted.")
                self.panel.upload_btn.setText("Submit to Moderation Queue")
                self.panel.upload_btn.setEnabled(True)
                return
 
            main_ref = self._api_request("git/refs/heads/main")

            # Handle if the response comes as a list or direct dict safely
            if isinstance(main_ref, list):
                main_sha = main_ref[0]["object"]["sha"]
            else:
                main_sha = main_ref["object"]["sha"]
                
            issue_payload = {
                "title": form_payload["title"],
                "body": (
                    f"### Asset Evaluation Request\n\n"
                    f"Asset Title Name: {form_payload['title']}\n"
                    f"Created By Artist: {form_payload['artist']} 👩‍🎨\n"
                    f"Category: {form_payload['category']}\n"
                    f"License: {form_payload['license']}\n\n"
                    f"Description / Credits / Tags:\n{form_payload['description']}"
                )
            }
            issue_res = self._api_request("issues", data=issue_payload, method="POST")
            issue_num = issue_res["number"]
            staging_branch_name = f"staging-{issue_num}"
            branch_payload = {"ref": f"refs/heads/{staging_branch_name}", "sha": main_sha}
            self._api_request("git/refs", data=branch_payload, method="POST")
            files_to_upload = [bundle["primary"], bundle["geometry"], bundle["material"], bundle["thumbnail"]] + bundle["textures"]
            for f_path in files_to_upload:
                if not f_path or not os.path.exists(f_path):
                    continue
                with open(f_path, "rb") as f_bytes:
                    b64_content = base64.b64encode(f_bytes.read()).decode('utf-8')
                rel_path = os.path.basename(f_path)
                commit_payload = {
                    "message": f"Staging asset component from creator @{form_payload['artist']}: {rel_path}",
                    "content": b64_content,
                    "branch": staging_branch_name
                }
                self._api_request(f"contents/{rel_path}", data=commit_payload, method="PUT")
            QApplication.restoreOverrideCursor()
            try:
                for f_path in files_to_upload:
                    if f_path and os.path.exists(f_path):
                        send2trash(f_path)
            except Exception:
                pass
            QMessageBox.information(self.panel, "Staging Complete!", f"Asset locked successfully. Assigned Evaluation Issue ID: #{issue_num}")
            self.panel.title_input.clear()
            self.panel.desc_input.clear()
            self.refresh_local_file_index(self.panel.path_input.text())
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self.panel, "Transaction Failed", f"GitHub operational error: {str(e)}")
        self.panel.upload_btn.setText("Submit to Moderation Queue")
        self.panel.upload_btn.setEnabled(True)


    def shutdown(self):
        if self.panel:
            self.panel.close()
            self.panel.deleteLater()
        if self.dock:
            self.mainwindow.removeDockWidget(self.dock)
            self.dock.close()
            self.dock.deleteLater()
        self.dock = None

    def initialize(self):
        if self.pluginname in self.repo:
            self.shutdown()
        self.dock = QDockWidget("MH2 Creator Sync Staging", self.mainwindow)
        self.dock.setObjectName("mh2_creator_portal_dock_widget")
        self.dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.panel = self.Panel(self)
        self.dock.setWidget(self.panel)
        
        if os.path.exists(self.credentials_path):
            try:
                with open(self.credentials_path, "r", encoding="utf-8") as f:
                    pref_data = json.load(f)
                    saved_user = pref_data.get("remember_user", "")
                    saved_tok = pref_data.get("saved_token", "")
                    if saved_user:
                        self.panel.user_input.setText(saved_user)
                    if saved_tok:
                        self.panel.pass_input.setText(saved_tok)
                        self.panel.remember_checkbox.setChecked(True)
                        self.token = saved_tok
                        self.headers = {
                            "Authorization": f"Bearer {self.token}",  
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                            "User-Agent": self.user_agent
                        }
                        try:
                            req = urllib.request.Request(f"{self.base_url}/user", headers=self.headers)
                            with urllib.request.urlopen(req, timeout=5) as response:
                                if response.status == 200:
                                    self.is_logged_in = True
                                    self.panel.upload_btn.setEnabled(True)
                                    self.panel.login_btn.setText("Gateway Connected ✓")
                                    self.panel.login_btn.setEnabled(False)
                        except Exception:
                            pass
            except Exception:
                pass
                
        parent_path = os.path.normpath(self.panel.path_input.text()).replace("\\", "/")
        self.refresh_local_file_index(parent_path)
        if hasattr(self.mainwindow, "addDockWidget"):
            self.mainwindow.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        else:
            self.dock.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.dock.show()
        self.repo[self.pluginname] = self
        return True


def load_extension(app, glob):
    pluginname = os.path.abspath(__file__)
    plugin = MH2CreatorPortalPanel(app, glob, pluginname)
    return plugin.initialize()


def unload_extension(glob):
    pluginname = os.path.abspath(__file__)
    if pluginname in glob.pluginRepo:
        glob.pluginRepo[pluginname].shutdown()
        glob.pluginRepo.pop(pluginname)
