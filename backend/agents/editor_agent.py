import os
import io
import textwrap
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as canvas_module
from PIL import Image as PILImage


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def sanitize_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in (" ", "_", "-") else "_" for c in name).strip()


# ──────────────────────────────────────────────────────────────────────────────
# Font Registration
# ──────────────────────────────────────────────────────────────────────────────
def _register_fonts():
    BODY = "Times-Roman"
    BODY_BOLD = "Times-Bold"
    BODY_ITALIC = "Times-Italic"
    TITLE = "Times-Bold"

    georgia_regular = ["C:\\Windows\\Fonts\\georgia.ttf", "C:\\Windows\\Fonts\\Georgia.ttf"]
    georgia_bold    = ["C:\\Windows\\Fonts\\georgiab.ttf"]
    georgia_italic  = ["C:\\Windows\\Fonts\\georgiai.ttf"]

    try:
        for p in georgia_regular:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("Georgia", p))
                BODY = "Georgia"
                break
        for p in georgia_bold:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("Georgia-Bold", p))
                BODY_BOLD = "Georgia-Bold"
                TITLE = "Georgia-Bold"
                break
        for p in georgia_italic:
            if os.path.exists(p):
                pdfmetrics.registerFont(TTFont("Georgia-Italic", p))
                BODY_ITALIC = "Georgia-Italic"
                break
    except Exception:
        pass

    return BODY, BODY_BOLD, BODY_ITALIC, TITLE


BODY_FONT, BODY_FONT_BOLD, BODY_FONT_ITALIC, TITLE_FONT = _register_fonts()


# ──────────────────────────────────────────────────────────────────────────────
# Colour Palette
# ──────────────────────────────────────────────────────────────────────────────
C_LEATHER     = colors.HexColor("#4A352C") # Dark brown leather cover
C_CREAM       = colors.HexColor("#FFFCF7") # Warm cream page background
C_CREASE_DARK = colors.HexColor("#00000033") 
C_CREASE_LITE = colors.HexColor("#00000005") 
C_SPINE_TUBE  = colors.HexColor("#8B7355") # The visible spine tube in the middle
C_BORDER      = colors.HexColor("#E8DED6") # Page edge
C_NOTE_LINE   = colors.HexColor("#D8C8B8") # Notebook lines
C_RED_MARG    = colors.HexColor("#EF444455") # Red margin line
C_TEXT        = colors.HexColor("#4A4A4A") # Text color
C_PILL_BG     = colors.HexColor("#F0E8DD") # Page indicator pill background
C_PILL_TEXT   = colors.HexColor("#8B7355") # Page indicator pill text

# Cover colors
C_COVER_DRK = C_CREAM  # Left inner cover background
C_COVER_PLM = colors.HexColor("#23102E")  # Deep purple for the cover
C_GOLD      = colors.HexColor("#FFD700")
C_GOLD_LGT  = colors.HexColor("#F5DEB3")

# ──────────────────────────────────────────────────────────────────────────────
# Geometry
# ──────────────────────────────────────────────────────────────────────────────
PAGE_W, PAGE_H = landscape(A4)   # 841.89 × 595.28 pts
# Make the leather background fill the entire PDF page or give it a small padding
LEATHER_PAD = 12
SPINE_WIDTH = 8
PAGE_CORNER_RADIUS = 10

# Calculate page sizes
# The canvas is PAGE_W x PAGE_H
# The two pages sit inside the leather pad
PAGE_Y = LEATHER_PAD
PAGE_H_INNER = PAGE_H - 2 * LEATHER_PAD
PAGE_W_INNER = (PAGE_W - 2 * LEATHER_PAD - SPINE_WIDTH) / 2

LEFT_PAGE_X = LEATHER_PAD
RIGHT_PAGE_X = LEATHER_PAD + PAGE_W_INNER + SPINE_WIDTH

# ──────────────────────────────────────────────────────────────────────────────
# Drawing functions
# ──────────────────────────────────────────────────────────────────────────────
def _draw_leather_bg(c):
    """Fill the base with the dark brown leather cover color."""
    c.setFillColor(C_LEATHER)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)


def _draw_page_shape(c, x, y, width, height, is_left=True):
    """Draw a cream page with rounded outer corners and sharp inner corners."""
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(1)

    r = PAGE_CORNER_RADIUS

    if is_left:
        # Draw full rounded rectangle for the page
        c.setFillColor(C_CREAM)
        c.roundRect(x, y, width, height, r, fill=1, stroke=1)
        # Override the right edge to be perfectly sharp
        c.rect(x + width - r, y, r, height, fill=1, stroke=0)
        # Redraw the borders that were covered by the sharp rectangle
        c.line(x + width - r, y + height, x + width, y + height) # top
        c.line(x + width - r, y, x + width, y) # bottom
        c.line(x + width, y, x + width, y + height) # right side
    else:
        # Draw full rounded rectangle for the page
        c.setFillColor(C_CREAM)
        c.roundRect(x, y, width, height, r, fill=1, stroke=1)
        # Override the left edge to be perfectly sharp
        c.rect(x, y, r, height, fill=1, stroke=0)
        # Redraw the borders that were covered by the sharp rectangle
        c.line(x, y + height, x + r, y + height) # top
        c.line(x, y, x + r, y) # bottom
        c.line(x, y, x, y + height) # left side

def _draw_spine_crease(c):
    """Draw the book spine and the crease shadows."""
    # The center is PAGE_W / 2
    cx = PAGE_W / 2
    
    # Shadow on the left page fading left
    left_shadow_w = 40
    for i in range(left_shadow_w):
        alpha = int((1.0 - (i / left_shadow_w)) * 12)
        c.setFillColor(colors.Color(0, 0, 0, alpha/255.0))
        c.rect(cx - SPINE_WIDTH/2 - i - 1, PAGE_Y, 1, PAGE_H_INNER, fill=1, stroke=0)

    # Shadow on the right page fading right
    right_shadow_w = 40
    for i in range(right_shadow_w):
        alpha = int((1.0 - (i / right_shadow_w)) * 12)
        c.setFillColor(colors.Color(0, 0, 0, alpha/255.0))
        c.rect(cx + SPINE_WIDTH/2 + i, PAGE_Y, 1, PAGE_H_INNER, fill=1, stroke=0)

    # The central spine tube
    c.setFillColor(colors.HexColor("#7a5d43"))
    c.rect(cx - SPINE_WIDTH/2, 0, SPINE_WIDTH, PAGE_H, fill=1, stroke=0)
    
    # Highlight on spine
    c.setFillColor(colors.HexColor("#8e7259"))
    c.rect(cx - 1, 0, 2, PAGE_H, fill=1, stroke=0)

def _draw_frame(c):
    """Draw the full open-book UI frame."""
    _draw_leather_bg(c)
    
    # Left page
    _draw_page_shape(c, LEFT_PAGE_X, PAGE_Y, PAGE_W_INNER, PAGE_H_INNER, is_left=True)
    
    # Right page
    _draw_page_shape(c, RIGHT_PAGE_X, PAGE_Y, PAGE_W_INNER, PAGE_H_INNER, is_left=False)
    
    # Spine crease
    _draw_spine_crease(c)

def _draw_pill(c, text, x_center, y_center):
    """Draw a rounded pill with text."""
    c.setFont(BODY_FONT_ITALIC, 10.5)
    text_width = c.stringWidth(text, BODY_FONT_ITALIC, 10.5)
    pill_w = text_width + 40
    pill_h = 24
    
    pill_x = x_center - pill_w / 2
    pill_y = y_center - pill_h / 2
    
    c.setFillColor(C_PILL_BG)
    c.setStrokeColor(colors.HexColor("#E0D8CC"))
    c.setLineWidth(1)
    c.roundRect(pill_x, pill_y, pill_w, pill_h, radius=12, fill=1, stroke=1)
    
    c.setFillColor(C_PILL_TEXT)
    c.drawCentredString(x_center, pill_y + 7.5, text)

# ──────────────────────────────────────────────────────────────────────────────
# Cover Page
# ──────────────────────────────────────────────────────────────────────────────
def _draw_cover_page(c, story_data, images_dir):
    """Draw the book cover and include the final story image on the left."""
    _draw_leather_bg(c)

    # Left page
    _draw_page_shape(c, LEFT_PAGE_X, PAGE_Y, PAGE_W_INNER, PAGE_H_INNER, is_left=True)
    
    # Right page
    _draw_page_shape(c, RIGHT_PAGE_X, PAGE_Y, PAGE_W_INNER, PAGE_H_INNER, is_left=False)
    _draw_spine_crease(c)
    
    c.setFillColor(C_COVER_DRK)
    c.roundRect(LEFT_PAGE_X, PAGE_Y, PAGE_W_INNER, PAGE_H_INNER, PAGE_CORNER_RADIUS, fill=1, stroke=0)
    c.rect(LEFT_PAGE_X + PAGE_W_INNER - PAGE_CORNER_RADIUS, PAGE_Y, PAGE_CORNER_RADIUS, PAGE_H_INNER, fill=1, stroke=0) # sharp inner
    
    c.setFillColor(C_COVER_PLM)
    c.roundRect(RIGHT_PAGE_X, PAGE_Y, PAGE_W_INNER, PAGE_H_INNER, PAGE_CORNER_RADIUS, fill=1, stroke=0)
    c.rect(RIGHT_PAGE_X, PAGE_Y, PAGE_CORNER_RADIUS, PAGE_H_INNER, fill=1, stroke=0) # sharp inner

    # ── Left half: last image ─────────────────────────────────────────
    scenes = story_data.get("scenes", [])
    if scenes:
        last_img_path = scenes[-1].get("image_path", "")
        if last_img_path:
            abs_img = os.path.join(images_dir, os.path.basename(last_img_path))
            if os.path.exists(abs_img):
                try:
                    pil = PILImage.open(abs_img)
                    pw, ph = pil.size
                    
                    pad_vertical = 70
                    pad_horizontal = 60
                    avail_w = PAGE_W_INNER - 2 * pad_horizontal
                    avail_h = PAGE_H_INNER - 2 * pad_vertical
                    
                    ratio = min(avail_w / pw, avail_h / ph)
                    dw, dh = pw * ratio, ph * ratio
                    
                    dx = LEFT_PAGE_X + (PAGE_W_INNER - dw) / 2
                    dy = PAGE_Y + (PAGE_H_INNER - dh) / 2

                    # White photo mat
                    mat = 8
                    c.setFillColor(colors.white)
                    c.rect(dx - mat, dy - mat, dw + 2*mat, dh + 2*mat, fill=1, stroke=0)
                    
                    # Thin border around mat
                    c.setStrokeColor(colors.HexColor("#A090A0"))
                    c.setLineWidth(0.5)
                    c.rect(dx - mat, dy - mat, dw + 2*mat, dh + 2*mat, fill=0, stroke=1)

                    c.drawImage(abs_img, dx, dy, width=dw, height=dh, mask="auto")
                except Exception as ex:
                    print(f"Cover img error: {ex}")

    # ── Right half: title ─────────────────────────────────────────
    mid_y = PAGE_Y + PAGE_H_INNER / 2
    pad = 40
    
    title = story_data.get("title", "Untitled Story")
    cx = RIGHT_PAGE_X + PAGE_W_INNER / 2
    font_size = 30 if len(title) < 24 else 24 if len(title) < 40 else 20
    c.setFont(TITLE_FONT, font_size)
    c.setFillColor(C_GOLD_LGT)
    
    words = title.split()
    lines_out, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if c.stringWidth(test, TITLE_FONT, font_size) < PAGE_W_INNER - 80:
            cur = test
        else:
            if cur: lines_out.append(cur)
            cur = w
    if cur: lines_out.append(cur)
    
    lh = font_size * 1.4
    
    # Calculate exactly where the text block starts and ends
    # ty is the baseline of the first line
    ty_start = mid_y + 10 + (len(lines_out) * lh) / 2
    
    # Draw decorative lines dynamically above and below the text block
    c.setStrokeColor(C_GOLD_LGT)
    c.setLineWidth(1)
    
    # Top line (15pt above the cap height of the first line)
    top_line_y = ty_start + (font_size * 0.8) + 15
    c.line(RIGHT_PAGE_X + pad, top_line_y, RIGHT_PAGE_X + PAGE_W_INNER - pad, top_line_y)
    
    # Bottom line (25pt below the baseline of the last line)
    bottom_line_y = ty_start - ((len(lines_out) - 1) * lh) - 25
    c.line(RIGHT_PAGE_X + pad, bottom_line_y, RIGHT_PAGE_X + PAGE_W_INNER - pad, bottom_line_y)

    # Draw the text
    ty = ty_start
    for ln in lines_out:
        c.drawCentredString(cx, ty, ln)
        ty -= lh

    # Author text positioned dynamically below the bottom line
    c.setFont(BODY_FONT_ITALIC, 12)
    c.setFillColor(colors.HexColor("#FFFFFFAA"))
    c.drawCentredString(cx, bottom_line_y - 20, "Authored by Magic & MyAIStorybook")

    _draw_pill(c, "Cover Page", RIGHT_PAGE_X + PAGE_W_INNER / 2, PAGE_Y + 50)


# ──────────────────────────────────────────────────────────────────────────────
# Scene Page
# ──────────────────────────────────────────────────────────────────────────────
def _draw_scene_page(c, scene, scene_index, total_scenes, images_dir):
    _draw_frame(c)

    # ── LEFT PAGE: Illustration ───────────────────────────────────────────────
    img_path = scene.get("image_path", "")
    abs_img  = os.path.join(images_dir, os.path.basename(img_path)) if img_path else ""

    pad_vertical = 60
    pad_horizontal = 50

    avail_w = PAGE_W_INNER - 2 * pad_horizontal
    avail_h = PAGE_H_INNER - 2 * pad_vertical

    if abs_img and os.path.exists(abs_img):
        try:
            pil = PILImage.open(abs_img)
            pw, ph = pil.size
            ratio = min(avail_w / pw, avail_h / ph)
            dw, dh = pw * ratio, ph * ratio
            
            # Center it
            dx = LEFT_PAGE_X + (PAGE_W_INNER - dw) / 2
            dy = PAGE_Y + (PAGE_H_INNER - dh) / 2

            # Drop shadow (soft grey behind image)
            shadow_offset = 6
            c.setFillColor(colors.HexColor("#0000001A"))
            c.rect(dx + shadow_offset, dy - shadow_offset, dw, dh, fill=1, stroke=0)

            # White photo mat
            mat = 12
            c.setFillColor(colors.white)
            c.rect(dx - mat, dy - mat, dw + 2*mat, dh + 2*mat, fill=1, stroke=0)
            
            # Thin delicate border around the mat
            c.setStrokeColor(colors.HexColor("#E0D8CC"))
            c.setLineWidth(0.5)
            c.rect(dx - mat, dy - mat, dw + 2*mat, dh + 2*mat, fill=0, stroke=1)

            c.drawImage(abs_img, dx, dy, width=dw, height=dh, mask="auto")
        except Exception as ex:
            print(f"Scene img error: {ex}")

    # ── RIGHT PAGE: Text ──────────────────────────────────────────────────────
    TEXT_PAD_L   = 55
    TEXT_PAD_R   = 45
    TEXT_PAD_TOP = 65
    TEXT_PAD_BOT = 100 # leave space for pill

    # Content boundaries
    content_x = RIGHT_PAGE_X + TEXT_PAD_L
    content_y = PAGE_Y + TEXT_PAD_BOT
    content_w = PAGE_W_INNER - TEXT_PAD_L - TEXT_PAD_R
    content_h = PAGE_H_INNER - TEXT_PAD_TOP - TEXT_PAD_BOT

    # Notebook ruling configuration to perfectly match the UI text placement
    font_size = 14
    leading = 32 # 32 points between lines

    # Red left margin line
    margin_line_x = content_x - 12
    c.setStrokeColor(C_RED_MARG)
    c.setLineWidth(1)
    c.line(margin_line_x, PAGE_Y + 50, margin_line_x, PAGE_Y + PAGE_H_INNER - 40)

    # Calculate layout of text with auto-scaling to prevent overflow
    text_content = scene.get("text", "")
    words = text_content.split()
    
    # Try progressively smaller font sizes until text fits in the content area
    for font_size in [14, 13, 12, 11, 10]:
        leading = int(font_size * 2.3)  # Proportional leading
        
        wrapped = []
        cur = ""
        first_line = True
        for word in words:
            test = (cur + " " + word).strip() if cur else ("       " + word if first_line else word)
            if c.stringWidth(test, BODY_FONT, font_size) <= content_w:
                cur = test
            else:
                if cur:
                    wrapped.append(cur)
                    first_line = False
                cur = word
        if cur:
            wrapped.append(cur)
        
        # Check if text fits within available content height
        total_text_height = len(wrapped) * leading
        if total_text_height <= content_h or font_size == 10:
            break  # Fits, or we've hit minimum font size

    # Draw lines and text aligned exactly on the lines
    y_pos = PAGE_Y + PAGE_H_INNER - TEXT_PAD_TOP
    
    # Calculate how many lines we need to draw notebook rulings for
    # We want to fill most of the page with rulings, even if text is shorter
    num_rulings = max(len(wrapped), int(content_h / leading))
    
    c.setFont(BODY_FONT, font_size)
    c.setFillColor(C_TEXT)

    for i in range(num_rulings):
        # Stop drawing if we've gone below the content area
        if y_pos - 6 < PAGE_Y + TEXT_PAD_BOT - 20:
            break
            
        # Draw ruling line
        c.setStrokeColor(C_NOTE_LINE)
        c.setLineWidth(0.5)
        
        # Notebook line starts slightly before the red line, ends slightly before right edge
        c.line(margin_line_x - 10, y_pos - 6, RIGHT_PAGE_X + PAGE_W_INNER - 20, y_pos - 6)
        
        # Draw text if available
        if i < len(wrapped):
            c.drawString(content_x, y_pos, wrapped[i])
            
        y_pos -= leading

    # ── Page Indicator Pill ───────────────────────────────────────────────────
    pill_text = f"Page {scene_index} of {total_scenes}"
    pill_cx = RIGHT_PAGE_X + PAGE_W_INNER / 2
    pill_cy = PAGE_Y + 45
    _draw_pill(c, pill_text, pill_cx, pill_cy)


# ──────────────────────────────────────────────────────────────────────────────
# Main Export Function
# ──────────────────────────────────────────────────────────────────────────────
def export_pdf(story_data: dict, output_filename: str) -> str:
    """
    Export the story as a storybook PDF exactly matching the open-book UI.
    """
    base_dir     = os.path.dirname(__file__)
    project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    generated    = os.path.join(project_root, "generated")
    exports_dir  = os.path.join(generated, "exports")
    images_dir   = os.path.join(generated, "images")
    os.makedirs(exports_dir, exist_ok=True)

    pdf_path = os.path.join(exports_dir, output_filename)
    scenes   = story_data.get("scenes", [])

    c = canvas_module.Canvas(pdf_path, pagesize=landscape(A4))
    c.setTitle(story_data.get("title", "Storybook"))

    # Cover page
    _draw_cover_page(c, story_data, images_dir)
    c.showPage()

    # Scene pages
    total = len(scenes)
    for i, scene in enumerate(scenes, start=1):
        _draw_scene_page(c, scene, scene_index=i, total_scenes=total, images_dir=images_dir)
        c.showPage()

    c.save()
    print(f"PDF saved: {pdf_path}")
    return pdf_path


# ──────────────────────────────────────────────────────────────────────────────
# EditorAgent
# ──────────────────────────────────────────────────────────────────────────────
class EditorAgent:
    def __init__(self, export_dir: str = None):
        backend_dir  = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(backend_dir))
        generated    = os.path.join(project_root, "generated")
        self.export_dir = os.path.join(generated, "exports")
        os.makedirs(self.export_dir, exist_ok=True)

    def edit_story(self, story_dict: Dict[str, Any]):
        story_dict["meta"] = {
            "edited_at": datetime.utcnow().isoformat() + "Z",
            "editor_version": "0.9",
        }
        story_dict["finalized"] = True
        return story_dict, "Edited and packaged"
