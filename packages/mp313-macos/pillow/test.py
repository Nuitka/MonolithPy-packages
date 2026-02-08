"""
Basic sanity tests for pillow (PIL) package.
Tests C-backed functionality without extra dependencies.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageOps
import io


def test_image_creation():
    """Test image creation (C-backed)."""
    # Create RGB image
    img = Image.new('RGB', (100, 100), color='red')
    assert img.size == (100, 100)
    assert img.mode == 'RGB'
    
    # Create RGBA image
    img_rgba = Image.new('RGBA', (50, 50), color=(255, 0, 0, 128))
    assert img_rgba.mode == 'RGBA'
    
    # Create grayscale image
    img_gray = Image.new('L', (100, 100), color=128)
    assert img_gray.mode == 'L'


def test_pixel_access():
    """Test pixel access (C-backed)."""
    img = Image.new('RGB', (10, 10), color='white')
    
    # Get pixel
    pixel = img.getpixel((5, 5))
    assert pixel == (255, 255, 255)
    
    # Set pixel
    img.putpixel((5, 5), (255, 0, 0))
    assert img.getpixel((5, 5)) == (255, 0, 0)


def test_image_resize():
    """Test image resizing (C-backed)."""
    img = Image.new('RGB', (100, 100), color='blue')
    
    # Resize
    resized = img.resize((50, 50))
    assert resized.size == (50, 50)
    
    # Resize with different resampling
    resized_lanczos = img.resize((200, 200), Image.Resampling.LANCZOS)
    assert resized_lanczos.size == (200, 200)


def test_image_rotate():
    """Test image rotation (C-backed)."""
    img = Image.new('RGB', (100, 100), color='green')
    
    rotated = img.rotate(45)
    assert rotated.size == (100, 100)
    
    rotated_expand = img.rotate(45, expand=True)
    assert rotated_expand.size[0] > 100


def test_image_crop():
    """Test image cropping (C-backed)."""
    img = Image.new('RGB', (100, 100), color='yellow')
    
    cropped = img.crop((10, 10, 50, 50))
    assert cropped.size == (40, 40)


def test_image_filter():
    """Test image filters (C-backed)."""
    img = Image.new('RGB', (100, 100), color='purple')
    
    # Blur
    blurred = img.filter(ImageFilter.BLUR)
    assert blurred.size == img.size
    
    # Sharpen
    sharpened = img.filter(ImageFilter.SHARPEN)
    assert sharpened.size == img.size
    
    # Edge detection
    edges = img.filter(ImageFilter.FIND_EDGES)
    assert edges.size == img.size


def test_image_draw():
    """Test image drawing (C-backed)."""
    img = Image.new('RGB', (100, 100), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw rectangle
    draw.rectangle([10, 10, 50, 50], fill='red', outline='black')
    
    # Draw ellipse
    draw.ellipse([60, 60, 90, 90], fill='blue')
    
    # Draw line
    draw.line([0, 0, 100, 100], fill='green', width=2)
    
    assert img.getpixel((20, 30)) == (255, 0, 0)  # Red rectangle (not on diagonal line)


def test_image_enhance():
    """Test image enhancement (C-backed)."""
    img = Image.new('RGB', (100, 100), color='gray')
    
    # Brightness
    enhancer = ImageEnhance.Brightness(img)
    bright = enhancer.enhance(1.5)
    assert bright.size == img.size
    
    # Contrast
    enhancer = ImageEnhance.Contrast(img)
    contrast = enhancer.enhance(2.0)
    assert contrast.size == img.size


def test_image_convert():
    """Test image mode conversion (C-backed)."""
    img = Image.new('RGB', (100, 100), color='red')
    
    # Convert to grayscale
    gray = img.convert('L')
    assert gray.mode == 'L'
    
    # Convert to RGBA
    rgba = img.convert('RGBA')
    assert rgba.mode == 'RGBA'


def test_image_ops():
    """Test image operations (C-backed)."""
    img = Image.new('RGB', (100, 100), color='blue')
    
    # Flip
    flipped = ImageOps.flip(img)
    assert flipped.size == img.size
    
    # Mirror
    mirrored = ImageOps.mirror(img)
    assert mirrored.size == img.size
    
    # Invert
    inverted = ImageOps.invert(img)
    assert inverted.size == img.size


def test_image_save_load():
    """Test image save/load to bytes (C-backed codecs)."""
    img = Image.new('RGB', (100, 100), color='cyan')
    
    # Save to bytes (PNG)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Load from bytes
    loaded = Image.open(buffer)
    assert loaded.size == (100, 100)
    
    # Save to bytes (JPEG)
    buffer_jpg = io.BytesIO()
    img.save(buffer_jpg, format='JPEG')
    buffer_jpg.seek(0)
    
    loaded_jpg = Image.open(buffer_jpg)
    assert loaded_jpg.size == (100, 100)


if __name__ == "__main__":
    test_image_creation()
    test_pixel_access()
    test_image_resize()
    test_image_rotate()
    test_image_crop()
    test_image_filter()
    test_image_draw()
    test_image_enhance()
    test_image_convert()
    test_image_ops()
    test_image_save_load()
    print("All pillow tests passed!")

