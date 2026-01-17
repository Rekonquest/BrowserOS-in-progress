// Copyright 2024 The Chromium Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "chrome/browser/ui/views/file_upload_overlay.h"

#include <utility>

#include "base/base64.h"
#include "base/files/file_util.h"
#include "base/json/json_reader.h"
#include "base/json/json_writer.h"
#include "base/strings/string_util.h"
#include "base/strings/utf_string_conversions.h"
#include "base/task/thread_pool.h"
#include "content/public/browser/browser_context.h"
#include "content/public/browser/navigation_handle.h"
#include "content/public/browser/render_frame_host.h"
#include "content/public/browser/web_contents.h"
#include "net/base/filename_util.h"
#include "ui/gfx/geometry/insets.h"
#include "ui/views/background.h"
#include "ui/views/controls/webview/webview.h"
#include "ui/views/layout/fill_layout.h"

namespace {

// Height of the upload bar in pixels
constexpr int kUploadBarHeight = 80;

// Reads file content from disk on a background thread
std::pair<bool, std::string> ReadFileContent(const base::FilePath& file_path,
                                              bool as_base64) {
  std::string content;
  if (!base::ReadFileToString(file_path, &content)) {
    return {false, ""};
  }

  if (as_base64) {
    std::string encoded = base::Base64Encode(content);
    return {true, encoded};
  }

  return {true, content};
}

// Determines if a file type is an image
bool IsImageFile(const std::string& mime_type) {
  return base::StartsWith(mime_type, "image/",
                          base::CompareCase::INSENSITIVE_ASCII);
}

}  // namespace

// UploadedFile implementation
FileUploadOverlay::UploadedFile::UploadedFile() = default;

FileUploadOverlay::UploadedFile::UploadedFile(const std::string& name,
                                               const std::string& type,
                                               int64_t size,
                                               const std::string& content,
                                               bool is_image)
    : name(name),
      type(type),
      size(size),
      content(content),
      is_image(is_image) {}

FileUploadOverlay::UploadedFile::~UploadedFile() = default;

FileUploadOverlay::UploadedFile::UploadedFile(const UploadedFile& other) =
    default;

FileUploadOverlay::UploadedFile& FileUploadOverlay::UploadedFile::operator=(
    const UploadedFile& other) = default;

// FileUploadOverlay implementation
FileUploadOverlay::FileUploadOverlay() {
  SetLayoutManager(std::make_unique<views::FillLayout>());

  // Create WebView for the upload UI
  upload_ui_webview_ = AddChildView(std::make_unique<views::WebView>(
      /* browser_context= */ nullptr));

  LoadUploadUI();
}

FileUploadOverlay::~FileUploadOverlay() {
  if (target_web_contents_) {
    Observe(nullptr);
  }
}

void FileUploadOverlay::SetTargetWebContents(
    content::WebContents* target_web_contents) {
  if (target_web_contents_ == target_web_contents) {
    return;
  }

  if (target_web_contents_) {
    Observe(nullptr);
  }

  target_web_contents_ = target_web_contents;

  if (target_web_contents_) {
    Observe(target_web_contents_);
  }
}

void FileUploadOverlay::ShowUploadBar() {
  is_upload_bar_visible_ = true;
  if (upload_ui_webview_ && upload_ui_webview_->GetWebContents()) {
    upload_ui_webview_->GetWebContents()->GetPrimaryMainFrame()->ExecuteJavaScript(
        u"if (window.BrowserOSFileUpload) { "
        u"window.BrowserOSFileUpload.showBar(); }",
        base::NullCallback());
  }
}

void FileUploadOverlay::HideUploadBar() {
  is_upload_bar_visible_ = false;
  if (upload_ui_webview_ && upload_ui_webview_->GetWebContents()) {
    upload_ui_webview_->GetWebContents()->GetPrimaryMainFrame()->ExecuteJavaScript(
        u"if (window.BrowserOSFileUpload) { "
        u"window.BrowserOSFileUpload.hideBar(); }",
        base::NullCallback());
  }
}

void FileUploadOverlay::ToggleUploadBar() {
  if (is_upload_bar_visible_) {
    HideUploadBar();
  } else {
    ShowUploadBar();
  }
}

void FileUploadOverlay::ClearAllFiles() {
  uploaded_files_.clear();
  if (upload_ui_webview_ && upload_ui_webview_->GetWebContents()) {
    upload_ui_webview_->GetWebContents()->GetPrimaryMainFrame()->ExecuteJavaScript(
        u"if (window.BrowserOSFileUpload) { "
        u"window.BrowserOSFileUpload.clearAllFiles(); }",
        base::NullCallback());
  }
}

void FileUploadOverlay::AddFiles(const std::vector<base::FilePath>& file_paths) {
  for (const auto& file_path : file_paths) {
    ReadFileFromDisk(file_path);
  }
}

void FileUploadOverlay::InjectFilesIntoLLM() {
  if (!target_web_contents_ || uploaded_files_.empty()) {
    return;
  }

  std::string provider = DetectLLMProvider();

  for (const auto& file : uploaded_files_) {
    InjectFileContent(file);
  }
}

void FileUploadOverlay::Layout(PassKey pass_key) {
  views::View::Layout(pass_key);

  if (upload_ui_webview_) {
    // Make the upload UI overlay fill the entire view
    upload_ui_webview_->SetBounds(0, 0, width(), height());
  }
}

void FileUploadOverlay::OnThemeChanged() {
  views::View::OnThemeChanged();
  // The upload UI will automatically adapt to dark mode via CSS media queries
}

void FileUploadOverlay::WebContentsDestroyed() {
  target_web_contents_ = nullptr;
  Observe(nullptr);
}

void FileUploadOverlay::DidFinishLoad(
    content::RenderFrameHost* render_frame_host,
    const GURL& validated_url) {
  // Upload UI finished loading, we can now interact with it
}

void FileUploadOverlay::CloseContents(content::WebContents* source) {
  // Not used
}

content::WebContents* FileUploadOverlay::OpenURLFromTab(
    content::WebContents* source,
    const content::OpenURLParams& params,
    base::OnceCallback<void(content::NavigationHandle&)>
        navigation_handle_callback) {
  // Prevent the upload UI from navigating away
  return nullptr;
}

void FileUploadOverlay::LoadUploadUI() {
  if (!upload_ui_webview_) {
    return;
  }

  // Get the file:// URL for the upload bar HTML
  // In a real implementation, this would use chrome://resources/ or similar
  base::FilePath resources_dir;
  // TODO: Get actual resources directory from PathService
  // For now, construct a relative path
  base::FilePath upload_ui_path =
      base::FilePath(FILE_PATH_LITERAL("packages/browseros/resources/"
                                       "file_upload_bar.html"));

  GURL upload_ui_url = net::FilePathToFileURL(upload_ui_path);

  upload_ui_webview_->GetWebContents()->SetDelegate(this);
  upload_ui_webview_->LoadInitialURL(upload_ui_url);
}

void FileUploadOverlay::HandleFileUploadMessage(const std::string& message) {
  // Parse JSON message from the upload UI
  auto message_value = base::JSONReader::Read(message);
  if (!message_value || !message_value->is_dict()) {
    return;
  }

  const std::string* type = message_value->GetDict().FindString("type");
  if (!type) {
    return;
  }

  if (*type == "browseros:files-changed") {
    const base::Value::List* files = message_value->GetDict().FindList("files");
    if (files) {
      ProcessUploadedFiles(*files);
    }
  }
}

void FileUploadOverlay::ProcessUploadedFiles(
    const base::Value::List& files_data) {
  // This would be called when files are uploaded via the UI
  // The actual file data would come from the renderer process
  // For now, this is a placeholder for the communication flow
}

void FileUploadOverlay::ReadFileFromDisk(const base::FilePath& file_path) {
  // Determine if this is an image file
  std::string mime_type;
  // TODO: Use net::GetMimeTypeFromFile() for proper MIME type detection

  bool is_image = false;
  std::string extension = file_path.Extension();
  if (extension == ".png" || extension == ".jpg" || extension == ".jpeg" ||
      extension == ".gif" || extension == ".webp" || extension == ".svg") {
    is_image = true;
    mime_type = "image/" + extension.substr(1);
  }

  // Read file on background thread
  base::ThreadPool::PostTaskAndReplyWithResult(
      FROM_HERE,
      {base::MayBlock(), base::TaskPriority::USER_VISIBLE},
      base::BindOnce(&ReadFileContent, file_path, is_image),
      base::BindOnce(
          [](base::WeakPtr<FileUploadOverlay> overlay,
             const base::FilePath& path,
             const std::string& mime_type,
             bool is_image,
             std::pair<bool, std::string> result) {
            if (!overlay || !result.first) {
              return;
            }

            UploadedFile file;
            file.name = path.BaseName().AsUTF8Unsafe();
            file.type = mime_type;
            file.size = result.second.length();
            file.content = result.second;
            file.is_image = is_image;

            overlay->uploaded_files_.push_back(std::move(file));
          },
          weak_ptr_factory_.GetWeakPtr(),
          file_path,
          mime_type,
          is_image));
}

void FileUploadOverlay::InjectFileContent(const UploadedFile& file) {
  if (!target_web_contents_) {
    return;
  }

  std::string provider = DetectLLMProvider();
  std::string injection_js = GetInjectionJavaScript(provider, file);

  if (injection_js.empty()) {
    return;
  }

  target_web_contents_->GetPrimaryMainFrame()->ExecuteJavaScript(
      base::UTF8ToUTF16(injection_js),
      base::NullCallback());
}

std::string FileUploadOverlay::DetectLLMProvider() const {
  if (!target_web_contents_) {
    return "unknown";
  }

  GURL url = target_web_contents_->GetLastCommittedURL();
  std::string host = url.host();

  if (host.find("chatgpt.com") != std::string::npos ||
      host.find("openai.com") != std::string::npos) {
    return "chatgpt";
  } else if (host.find("claude.ai") != std::string::npos ||
             host.find("anthropic.com") != std::string::npos) {
    return "claude";
  } else if (host.find("gemini.google.com") != std::string::npos ||
             host.find("bard.google.com") != std::string::npos) {
    return "gemini";
  } else if (host.find("copilot.microsoft.com") != std::string::npos ||
             host.find("bing.com/chat") != std::string::npos) {
    return "copilot";
  } else if (host.find("perplexity.ai") != std::string::npos) {
    return "perplexity";
  }

  return "generic";
}

std::string FileUploadOverlay::GetInjectionJavaScript(
    const std::string& provider,
    const UploadedFile& file) const {
  std::string js;

  if (file.is_image) {
    // For images, we need to trigger the file upload mechanism or
    // insert the image as a data URL
    std::string data_url =
        "data:" + file.type + ";base64," + file.content;

    if (provider == "chatgpt") {
      js = R"(
        (function() {
          const dataUrl = ')" + data_url + R"(';
          const fileName = ')" + file.name + R"(';

          // Try to find the file input element
          const fileInput = document.querySelector('input[type="file"]');
          if (fileInput) {
            // Convert data URL to Blob and File
            fetch(dataUrl)
              .then(res => res.blob())
              .then(blob => {
                const file = new File([blob], fileName, { type: ')" + file.type + R"(' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;

                // Trigger change event
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
              });
          }
        })();
      )";
    } else if (provider == "claude") {
      js = R"(
        (function() {
          const dataUrl = ')" + data_url + R"(';
          const fileName = ')" + file.name + R"(';

          // Try to insert into Claude's input
          const fileInput = document.querySelector('input[type="file"]');
          if (fileInput) {
            fetch(dataUrl)
              .then(res => res.blob())
              .then(blob => {
                const file = new File([blob], fileName, { type: ')" + file.type + R"(' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;

                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
              });
          }
        })();
      )";
    } else {
      // Generic approach for other providers
      js = R"(
        (function() {
          const dataUrl = ')" + data_url + R"(';
          const fileName = ')" + file.name + R"(';

          const fileInput = document.querySelector('input[type="file"]');
          if (fileInput) {
            fetch(dataUrl)
              .then(res => res.blob())
              .then(blob => {
                const file = new File([blob], fileName, { type: ')" + file.type + R"(' });
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;

                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
              });
          }
        })();
      )";
    }
  } else {
    // For text files, we can insert the content directly into the input
    std::string escaped_content = file.content;
    // TODO: Proper JavaScript string escaping
    base::ReplaceChars(escaped_content, "\\", "\\\\", &escaped_content);
    base::ReplaceChars(escaped_content, "'", "\\'", &escaped_content);
    base::ReplaceChars(escaped_content, "\n", "\\n", &escaped_content);
    base::ReplaceChars(escaped_content, "\r", "\\r", &escaped_content);

    js = R"(
      (function() {
        const content = ')" + escaped_content + R"(';
        const fileName = ')" + file.name + R"(';

        // Try to find the text input or textarea
        const input = document.querySelector('textarea[placeholder*="message"], textarea[placeholder*="Message"], div[contenteditable="true"]');
        if (input) {
          const prefix = '--- File: ' + fileName + ' ---\n';
          const suffix = '\n--- End of file ---\n';

          if (input.tagName === 'TEXTAREA') {
            input.value = input.value + prefix + content + suffix;
            input.dispatchEvent(new Event('input', { bubbles: true }));
          } else {
            // For contenteditable divs
            const pre = document.createElement('pre');
            pre.textContent = prefix + content + suffix;
            input.appendChild(pre);
            input.dispatchEvent(new Event('input', { bubbles: true }));
          }
        }
      })();
    )";
  }

  return js;
}
