#include "chrome/browser/ui/views/tool_usage_indicator_overlay.h"

#include "base/strings/utf_string_conversions.h"
#include "ui/gfx/canvas.h"
#include "ui/gfx/geometry/insets.h"
#include "ui/gfx/geometry/rect.h"
#include "ui/views/border.h"
#include "ui/views/background.h"

namespace views {

namespace {

// Default animation duration for the pulse effect (in milliseconds)
constexpr int kPulseAnimationDurationMs = 2000;

// Color definitions for tool types
constexpr SkColor kBrowserToolColor = SkColorSetRGB(66, 133, 244);    // Blue
constexpr SkColor kFileSystemToolColor = SkColorSetRGB(52, 168, 83);  // Green
constexpr SkColor kTerminalToolColor = SkColorSetRGB(251, 188, 5);    // Yellow
constexpr SkColor kAPIToolColor = SkColorSetRGB(234, 67, 53);         // Red
constexpr SkColor kGenericToolColor = SkColorSetRGB(66, 133, 244);    // Blue

}  // namespace

ToolUsageIndicatorOverlay::ToolUsageIndicatorOverlay() {
  SetVisible(false);

  // Create and configure the pulse animation
  pulse_animation_ = std::make_unique<gfx::SlideAnimation>(this);
  pulse_animation_->SetDuration(
      base::Milliseconds(kPulseAnimationDurationMs));
  pulse_animation_->SetTweenType(gfx::Tween::EASE_IN_OUT);

  // Make the overlay non-interactive
  SetCanProcessEventsWithinSubtree(false);
}

ToolUsageIndicatorOverlay::~ToolUsageIndicatorOverlay() = default;

void ToolUsageIndicatorOverlay::ShowToolUsage(
    ToolType type,
    const std::u16string& tool_name,
    const std::u16string& description) {
  current_tool_info_.type = type;
  current_tool_info_.tool_name = tool_name;
  current_tool_info_.description = description;

  is_showing_ = true;
  SetVisible(true);

  // Start the pulsing animation
  pulse_animation_->Show();

  // Request a repaint
  SchedulePaint();
}

void ToolUsageIndicatorOverlay::HideToolUsage() {
  is_showing_ = false;

  // Stop the animation
  pulse_animation_->Hide();

  // Hide the overlay after animation completes
  SetVisible(false);

  // Clear tool info
  current_tool_info_ = ToolUsageInfo();
}

void ToolUsageIndicatorOverlay::SetGlowIntensity(double intensity) {
  glow_intensity_ = std::clamp(intensity, 0.0, 1.0);
  SchedulePaint();
}

void ToolUsageIndicatorOverlay::OnPaint(gfx::Canvas* canvas) {
  if (!is_showing_) {
    return;
  }

  // Get the current animation value (0.0 to 1.0)
  double anim_value = pulse_animation_->GetCurrentValue();

  // Calculate pulsing opacity (oscillates between 0.3 and 1.0)
  // Using sine wave for smooth pulsing effect
  double phase = anim_value * 2.0 * 3.14159265359;  // One full cycle
  double pulse_factor = 0.65 + 0.35 * std::sin(phase);
  double opacity = pulse_factor * glow_intensity_;

  // Get the color for the current tool type
  SkColor base_color = GetToolTypeColor(current_tool_info_.type);

  // Create multiple layers for the glow effect
  gfx::Rect bounds = GetLocalBounds();

  // Outer glow (widest, most transparent)
  for (int i = 0; i < border_thickness_ * 2; ++i) {
    double layer_opacity = opacity * (1.0 - (i / (border_thickness_ * 2.0)));
    SkColor layer_color = SkColorSetA(base_color,
                                       static_cast<U8CPU>(255 * layer_opacity));

    gfx::Rect layer_rect = bounds;
    layer_rect.Inset(gfx::Insets(i));

    // Draw the border layer
    canvas->DrawRect(layer_rect, layer_color);
  }

  // Inner solid border
  SkColor solid_color = SkColorSetA(base_color,
                                     static_cast<U8CPU>(255 * opacity));
  gfx::Rect inner_rect = bounds;
  inner_rect.Inset(gfx::Insets(border_thickness_ * 2));

  cc::PaintFlags border_flags;
  border_flags.setColor(solid_color);
  border_flags.setStyle(cc::PaintFlags::kStroke_Style);
  border_flags.setStrokeWidth(border_thickness_);
  border_flags.setAntiAlias(true);

  canvas->DrawRect(inner_rect, border_flags);

  View::OnPaint(canvas);
}

gfx::Size ToolUsageIndicatorOverlay::CalculatePreferredSize() const {
  // The overlay should fill its parent
  return gfx::Size();
}

void ToolUsageIndicatorOverlay::Layout() {
  // Fill the entire parent view
  if (parent()) {
    SetBoundsRect(parent()->GetLocalBounds());
  }
  View::Layout();
}

void ToolUsageIndicatorOverlay::AnimationProgressed(
    const gfx::Animation* animation) {
  // Repaint on each animation frame
  SchedulePaint();
}

void ToolUsageIndicatorOverlay::AnimationEnded(const gfx::Animation* animation) {
  if (is_showing_) {
    // Loop the animation for continuous pulsing
    pulse_animation_->Show();
  }
}

SkColor ToolUsageIndicatorOverlay::GetToolTypeColor(ToolType type) const {
  switch (type) {
    case ToolType::BROWSER:
      return kBrowserToolColor;
    case ToolType::FILE_SYSTEM:
      return kFileSystemToolColor;
    case ToolType::TERMINAL:
      return kTerminalToolColor;
    case ToolType::API:
      return kAPIToolColor;
    case ToolType::GENERIC:
    default:
      return kGenericToolColor;
  }
}

}  // namespace views
