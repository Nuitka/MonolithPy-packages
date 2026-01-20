"""
Basic sanity tests for matplotlib package.
Tests C-backed functionality without extra dependencies.
Uses non-interactive backend to avoid display requirements.
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import matplotlib.path as mpath
import matplotlib.transforms as mtransforms


def test_figure_creation():
    """Test figure creation (C-backed)."""
    fig = plt.figure(figsize=(8, 6))
    assert fig is not None
    assert fig.get_figwidth() == 8
    assert fig.get_figheight() == 6
    plt.close(fig)


def test_basic_plot():
    """Test basic plotting (C-backed rendering)."""
    fig, ax = plt.subplots()
    
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    
    line, = ax.plot(x, y)
    assert line is not None
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Test Plot')
    
    plt.close(fig)


def test_scatter_plot():
    """Test scatter plot (C-backed)."""
    fig, ax = plt.subplots()
    
    x = np.random.rand(50)
    y = np.random.rand(50)
    colors = np.random.rand(50)
    sizes = 100 * np.random.rand(50)
    
    scatter = ax.scatter(x, y, c=colors, s=sizes)
    assert scatter is not None
    
    plt.close(fig)


def test_histogram():
    """Test histogram (C-backed)."""
    fig, ax = plt.subplots()
    
    data = np.random.randn(1000)
    n, bins, patches = ax.hist(data, bins=30)
    
    assert len(n) == 30
    assert len(bins) == 31
    
    plt.close(fig)


def test_bar_plot():
    """Test bar plot (C-backed)."""
    fig, ax = plt.subplots()
    
    categories = ['A', 'B', 'C', 'D']
    values = [10, 20, 15, 25]
    
    bars = ax.bar(categories, values)
    assert len(bars) == 4
    
    plt.close(fig)


def test_imshow():
    """Test image display (C-backed)."""
    fig, ax = plt.subplots()
    
    data = np.random.rand(10, 10)
    im = ax.imshow(data, cmap='viridis')
    
    assert im is not None
    
    plt.close(fig)


def test_contour():
    """Test contour plot (C-backed)."""
    fig, ax = plt.subplots()
    
    x = np.linspace(-3, 3, 50)
    y = np.linspace(-3, 3, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(X) * np.cos(Y)
    
    contour = ax.contour(X, Y, Z)
    assert contour is not None
    
    plt.close(fig)


def test_colormap():
    """Test colormap functionality (C-backed)."""
    cmap = cm.get_cmap('viridis')
    assert cmap is not None
    
    # Get color at specific value
    color = cmap(0.5)
    assert len(color) == 4  # RGBA


def test_path():
    """Test path operations (C-backed)."""
    vertices = np.array([
        [0, 0], [1, 0], [1, 1], [0, 1], [0, 0]
    ])
    codes = [mpath.Path.MOVETO, mpath.Path.LINETO, 
             mpath.Path.LINETO, mpath.Path.LINETO, mpath.Path.CLOSEPOLY]
    
    path = mpath.Path(vertices, codes)
    assert path is not None
    assert len(path.vertices) == 5


def test_transforms():
    """Test transform operations (C-backed)."""
    t = mtransforms.Affine2D()
    t.rotate_deg(45)
    t.translate(1, 2)
    
    assert t is not None


def test_canvas_rendering():
    """Test canvas rendering (C-backed AGG)."""
    fig = Figure(figsize=(4, 3))
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_subplot(111)
    
    ax.plot([1, 2, 3], [1, 4, 9])
    
    # Render to buffer
    canvas.draw()
    buf = canvas.buffer_rgba()
    assert buf is not None
    
    plt.close(fig)


if __name__ == "__main__":
    test_figure_creation()
    test_basic_plot()
    test_scatter_plot()
    test_histogram()
    test_bar_plot()
    test_imshow()
    test_contour()
    test_colormap()
    test_path()
    test_transforms()
    test_canvas_rendering()
    print("All matplotlib tests passed!")

