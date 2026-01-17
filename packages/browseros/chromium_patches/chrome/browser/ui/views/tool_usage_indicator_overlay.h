#ifndef CHROME_BROWSER_UI_VIEWS_TOOL_USAGE_INDICATOR_OVERLAY_H_
#define CHROME_BROWSER_UI_VIEWS_TOOL_USAGE_INDICATOR_OVERLAY_H_

#include "base/memory/raw_ptr.h"
#include "base/timer/timer.h"
#include "ui/views/view.h"
#include "ui/views/widget/widget.h"
#include "ui/gfx/animation/animation_delegate.h"
#include "ui/gfx/animation/slide_animation.h"

namespace views {

// ToolUsageIndicatorOverlay
//
// Displays a visual indicator overlay (glowing blue pulsing border) when AI
// models are actively using tools or browsing. Similar to Gemini and Comet's
// visual feedback for tool usage.
//
// Usage:
//   auto* overlay = new ToolUsageIndicatorOverlay();
//   parent_view->AddChildView(overlay);
//   overlay->ShowToolUsage(ToolUsageIndicatorOverlay::ToolType::BROWSER);
//   overlay->HideToolUsage();
class ToolUsageIndicatorOverlay : public views::View,
                                   public gfx::AnimationDelegate {
 public:
  enum class ToolType {
    BROWSER,       // Web browsing tool
    FILE_SYSTEM,   // File operations
    TERMINAL,      // Command execution
    API,           // API calls
    GENERIC,       // Other tools
  };

  struct ToolUsageInfo {
    ToolType type = ToolType::GENERIC;
    std::u16string tool_name;
    std::u16string description;
  };

  ToolUsageIndicatorOverlay();
  ToolUsageIndicatorOverlay(const ToolUsageIndicatorOverlay&) = delete;
  ToolUsageIndicatorOverlay& operator=(const ToolUsageIndicatorOverlay&) =
      delete;
  ~ToolUsageIndicatorOverlay() override;

  // Shows the tool usage indicator with specified tool information
  void ShowToolUsage(ToolType type,
                     const std::u16string& tool_name = std::u16string(),
                     const std::u16string& description = std::u16string());

  // Hides the tool usage indicator
  void HideToolUsage();

  // Returns whether the indicator is currently visible
  bool IsShowingToolUsage() const { return is_showing_; }

  // Sets the intensity of the glow effect (0.0 to 1.0)
  void SetGlowIntensity(double intensity);

  // views::View:
  void OnPaint(gfx::Canvas* canvas) override;
  gfx::Size CalculatePreferredSize() const override;
  void Layout() override;

  // gfx::AnimationDelegate:
  void AnimationProgressed(const gfx::Animation* animation) override;
  void AnimationEnded(const gfx::Animation* animation) override;

 private:
  // Creates the visual overlay with pulsing blue border
  void CreateOverlay();

  // Updates the overlay appearance based on animation state
  void UpdateOverlay();

  // Gets the color for the specified tool type
  SkColor GetToolTypeColor(ToolType type) const;

  // Animation for the pulsing glow effect
  std::unique_ptr<gfx::SlideAnimation> pulse_animation_;

  // Current tool usage information
  ToolUsageInfo current_tool_info_;

  // Whether the indicator is currently showing
  bool is_showing_ = false;

  // Current glow intensity (0.0 to 1.0)
  double glow_intensity_ = 0.8;

  // Border thickness in pixels
  int border_thickness_ = 4;

  // Timer for auto-hide if needed
  base::OneShotTimer auto_hide_timer_;
};

}  // namespace views

#endif  // CHROME_BROWSER_UI_VIEWS_TOOL_USAGE_INDICATOR_OVERLAY_H_
