// Copyright 2024 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#ifndef CHROME_BROWSER_UI_VIEWS_FILE_UPLOAD_OVERLAY_H_
#define CHROME_BROWSER_UI_VIEWS_FILE_UPLOAD_OVERLAY_H_

#include <memory>
#include <string>
#include <vector>

#include "base/memory/raw_ptr.h"
#include "base/memory/weak_ptr.h"
#include "content/public/browser/web_contents.h"
#include "content/public/browser/web_contents_delegate.h"
#include "content/public/browser/web_contents_observer.h"
#include "ui/views/controls/webview/webview.h"
#include "ui/views/view.h"

namespace views {
class WebView;
}  // namespace views

// FileUploadOverlay provides a universal file upload interface that works
// across all LLM providers in BrowserOS. It displays a file upload bar with
// drag-and-drop support, image previews, and automatic content injection.
//
// Usage:
//   auto* overlay = new FileUploadOverlay();
//   parent_view->AddChildView(overlay);
//   overlay->SetBounds(0, 0, parent_width, parent_height);
//   overlay->SetTargetWebContents(llm_provider_web_contents);
//
// The overlay will display a file upload bar at the bottom of the view and
// handle file uploads by injecting content into the target LLM provider's
// input field.
class FileUploadOverlay : public views::View,
                          public content::WebContentsObserver,
                          public content::WebContentsDelegate {
 public:
  // Represents an uploaded file
  struct UploadedFile {
    std::string name;
    std::string type;
    int64_t size;
    std::string content;  // Base64 encoded for images, plain text for others
    bool is_image;

    UploadedFile();
    UploadedFile(const std::string& name,
                 const std::string& type,
                 int64_t size,
                 const std::string& content,
                 bool is_image);
    ~UploadedFile();
    UploadedFile(const UploadedFile& other);
    UploadedFile& operator=(const UploadedFile& other);
  };

  FileUploadOverlay();
  FileUploadOverlay(const FileUploadOverlay&) = delete;
  FileUploadOverlay& operator=(const FileUploadOverlay&) = delete;
  ~FileUploadOverlay() override;

  // Sets the target WebContents where files will be injected
  void SetTargetWebContents(content::WebContents* target_web_contents);

  // Shows or hides the upload bar
  void ShowUploadBar();
  void HideUploadBar();
  void ToggleUploadBar();
  bool IsUploadBarVisible() const { return is_upload_bar_visible_; }

  // Gets the current list of uploaded files
  const std::vector<UploadedFile>& GetUploadedFiles() const {
    return uploaded_files_;
  }

  // Clears all uploaded files
  void ClearAllFiles();

  // Manually adds files (useful for programmatic uploads)
  void AddFiles(const std::vector<base::FilePath>& file_paths);

  // Injects the uploaded files into the target LLM provider
  void InjectFilesIntoLLM();

  // views::View:
  void Layout(PassKey) override;
  void OnThemeChanged() override;

  // content::WebContentsObserver:
  void WebContentsDestroyed() override;
  void DidFinishLoad(content::RenderFrameHost* render_frame_host,
                     const GURL& validated_url) override;

  // content::WebContentsDelegate:
  void CloseContents(content::WebContents* source) override;
  content::WebContents* OpenURLFromTab(
      content::WebContents* source,
      const content::OpenURLParams& params,
      base::OnceCallback<void(content::NavigationHandle&)>
          navigation_handle_callback) override;

 private:
  // Loads the file upload HTML UI
  void LoadUploadUI();

  // Handles messages from the upload UI JavaScript
  void HandleFileUploadMessage(const std::string& message);

  // Processes uploaded files
  void ProcessUploadedFiles(const base::Value::List& files_data);

  // Reads a file from disk
  void ReadFileFromDisk(const base::FilePath& file_path);

  // Injects file content into the target LLM provider's input
  void InjectFileContent(const UploadedFile& file);

  // Detects the LLM provider type from the target WebContents
  std::string DetectLLMProvider() const;

  // Gets the appropriate JavaScript injection code for the detected provider
  std::string GetInjectionJavaScript(const std::string& provider,
                                      const UploadedFile& file) const;

  // WebView containing the upload UI
  raw_ptr<views::WebView> upload_ui_webview_ = nullptr;

  // Target WebContents where files will be injected
  raw_ptr<content::WebContents> target_web_contents_ = nullptr;

  // List of uploaded files
  std::vector<UploadedFile> uploaded_files_;

  // Upload bar visibility state
  bool is_upload_bar_visible_ = true;

  // Weak pointer factory
  base::WeakPtrFactory<FileUploadOverlay> weak_ptr_factory_{this};
};

#endif  // CHROME_BROWSER_UI_VIEWS_FILE_UPLOAD_OVERLAY_H_
