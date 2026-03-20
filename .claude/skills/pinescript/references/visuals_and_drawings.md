# Pine Script Visuals & Drawings Reference

Comprehensive reference for all Pine Script visual output: plots, drawing objects (lines, boxes, labels, polylines, tables), fills, backgrounds, colors, and coordinate systems.

## Contents
- 1. Visual Output Categories
- 2. Coordinate Systems
- 3. Plot Functions (plot, plotshape, plotchar, plotarrow, plotbar, plotcandle)
- 4. Drawing Objects (line, box, label, polyline, table, linefill)
- 5. Fills and Backgrounds
- 6. Colors
- 7. Horizontal Levels (hline)
- 8. Z-Index and Layering
- 9. Object Limits and Garbage Collection
- 10. Display Parameter
- 11. UI Drawing Tools vs Pine Script Drawings
- 12. Common Patterns and Gotchas
- 13. Trade Drawer Pattern (TTE Project)

---

## 1. Visual Output Categories

Pine Script visuals fall into two categories:

**Plot-based outputs** — Fixed to the bar execution model. Cannot exist in local scopes (if/for/functions). One output per bar per call.
- `plot()`, `plotshape()`, `plotchar()`, `plotarrow()`, `plotbar()`, `plotcandle()`
- `hline()`, `fill()`, `bgcolor()`, `barcolor()`

**Drawing objects** — Created/modified/deleted dynamically. Can exist in any scope. Multiple objects per bar.
- `line.new()`, `box.new()`, `label.new()`, `polyline.new()`, `table.new()`, `linefill.new()`

**Key distinction**: Plots are declared once and output every bar. Drawing objects are created on specific bars and persist until deleted or garbage-collected.

---

## 2. Coordinate Systems

### X-Axis: bar_index vs time

Drawing objects (`line`, `box`, `label`, `polyline`) use `xloc` parameter:

| Mode | Value Type | Use When |
|------|-----------|----------|
| `xloc.bar_index` (default) | Integer bar index | Positioning relative to bars on chart |
| `xloc.bar_time` | UNIX timestamp (ms) | Positioning at specific times, future projections |

**bar_index limits**: ±10,000 bars past, +500 bars into future from current bar.

**xloc.bar_time**: No hard future limit, but drawings at times with no bars render at nearest available bar. Weekends/holidays create gaps — drawings span them visually.

### Y-Axis: Price Values

Always a price/value on the script's scale. For overlay indicators, this is the chart's price scale.

### chart.point Object

Unified coordinate container for `polyline.new()` and `label.new()`:
```pinescript
chart.point.from_index(bar_index, price)   // bar_index + price
chart.point.from_time(timestamp, price)    // time + price
```

### Label Y-Axis Positioning

Labels have additional `yloc` parameter:
- `yloc.price` (default) — uses `y` parameter for exact price
- `yloc.abovebar` — positions above bar's high (ignores `y`)
- `yloc.belowbar` — positions below bar's low (ignores `y`)

---

## 3. Plot Functions

### plot()

```pinescript
plot(series, title, color, linewidth, style, trackprice, histbase,
     offset, join, editable, show_last, display, format, precision,
     force_overlay) → plot
```

**series**: int/float value to plot each bar. Use `na` to create gaps.
**style options**: `plot.style_line`, `plot.style_stepline`, `plot.style_stepline_diamond`, `plot.style_histogram`, `plot.style_cross`, `plot.style_area`, `plot.style_areabr`, `plot.style_columns`, `plot.style_circles`, `plot.style_linebr`
**offset**: Shifts plot left (negative) or right (positive) by N bars.
**force_overlay**: `true` = render in main chart pane regardless of script's `overlay` setting.

**Critical**: `plot()` cannot exist inside `if`, `for`, `while`, or functions. Always declare in global scope. Control visibility with `na` values or conditional colors.

```pinescript
// WRONG — compile error
if condition
    plot(close)

// CORRECT — conditional via na
plot(condition ? close : na)
```

**Returns a plot ID** usable in `fill()`.

### plotshape()

```pinescript
plotshape(series, title, style, location, color, offset, text, textcolor,
          editable, size, show_last, display, format, precision, force_overlay) → void
```

**series**: bool, int, or float. Boolean `true` = show shape; `false`/`na` = hide.
**text**: **const string only** — cannot contain series values. Use `\n` for multi-line.
**size**: `size.tiny`, `size.small`, `size.normal`, `size.large`, `size.huge`, `size.auto`
**location**: `location.abovebar`, `location.belowbar`, `location.top`, `location.bottom`, `location.absolute`

**Shape styles**: `shape.xcross`, `shape.cross`, `shape.circle`, `shape.triangleup`, `shape.triangledown`, `shape.flag`, `shape.arrowup`, `shape.arrowdown`, `shape.square`, `shape.diamond`, `shape.labelup`, `shape.labeldown`

### plotchar()

```pinescript
plotchar(series, title, char, location, color, offset, text, textcolor,
         editable, size, show_last, display, format, precision, force_overlay) → void
```

**char**: Single Unicode character (const string).
**text**: **const string only** — same limitation as plotshape.

### plotarrow()

```pinescript
plotarrow(series, title, colorup, colordown, offset, minheight, maxheight,
          editable, show_last, display, format, precision, force_overlay) → void
```

**series**: int/float (NOT bool). Positive = up arrow, negative = down arrow, 0/na = no arrow.
**Arrow size**: Proportional to absolute series value, clamped between `minheight` and `maxheight` (pixels).

### plotbar() and plotcandle()

```pinescript
plotbar(open, high, low, close, title, color, editable, show_last, display, force_overlay) → void
plotcandle(open, high, low, close, title, color, wickcolor, editable, show_last, bordercolor, display) → void
```

Both require all four OHLC values. If any is `na`, no bar renders.
**Plot count**: Each call counts as at least 4 plots toward the 64-plot limit.
**Color**: Accepts series color for dynamic candle coloring.

---

## 4. Drawing Objects

### line.new()

```pinescript
line.new(x1, y1, x2, y2, xloc, extend, color, style, width) → series line
line.new(first_point, second_point, xloc, extend, color, style, width) → series line
```

**xloc**: `xloc.bar_index` (default) or `xloc.bar_time`
**extend**: `extend.none` (default), `extend.left`, `extend.right`, `extend.both`
**style**: `line.style_solid`, `line.style_dotted`, `line.style_dashed`, `line.style_arrow_left`, `line.style_arrow_right`, `line.style_arrow_both`
**width**: 1-4 pixels

**Setters**: `line.set_x1()`, `line.set_y1()`, `line.set_x2()`, `line.set_y2()`, `line.set_xy1()`, `line.set_xy2()`, `line.set_first_point()`, `line.set_second_point()`, `line.set_xloc()`, `line.set_extend()`, `line.set_color()`, `line.set_style()`, `line.set_width()`
**Getters**: `line.get_x1()`, `line.get_y1()`, `line.get_x2()`, `line.get_y2()`, `line.get_price()`
**Other**: `line.copy()`, `line.delete()`, `line.all` (read-only array of all visible lines)

**Vertical lines**: Set both x-coordinates to same bar, different y-values.
**Horizontal lines**: Set both y-coordinates to same price, different x-values.

### box.new()

```pinescript
box.new(left, top, right, bottom, border_color, border_width, border_style,
        extend, xloc, bgcolor, text, text_size, text_color, text_halign,
        text_valign, text_wrap, text_font_family) → series box
box.new(top_left, bottom_right, border_color, border_width, border_style,
        extend, xloc, bgcolor, text, text_size, text_color, text_halign,
        text_valign, text_wrap, text_font_family) → series box
```

**Coordinates**: Two diagonal corners (top-left x/y, bottom-right x/y).
**border_style**: `line.style_solid`, `line.style_dotted`, `line.style_dashed`
**text_halign**: `text.align_left`, `text.align_center`, `text.align_right`
**text_valign**: `text.align_top`, `text.align_center`, `text.align_bottom`
**text_wrap**: `text.wrap_auto`, `text.wrap_none`
**text**: **series string** — supports dynamic text (unlike plotshape/plotchar).
**bgcolor**: Fill color inside the box.

**Setters/Getters**: Full set of `.set_*()` and `.get_*()` methods for all properties.
**Other**: `box.copy()`, `box.delete()`, `box.all`

### label.new()

```pinescript
label.new(x, y, text, xloc, yloc, color, style, textcolor, size,
          textalign, tooltip, text_font_family, force_overlay, text_formatting) → series label
label.new(point, text, xloc, yloc, color, style, textcolor, size,
          textalign, tooltip, text_font_family, force_overlay, text_formatting) → series label
```

**text**: **series string** — supports dynamic content via `str.tostring()`.
**tooltip**: Series string shown on hover.
**text_formatting**: `text.format_none`, `text.format_bold`, `text.format_italic`, or combined with `+`.
**text_font_family**: `font.family_default`, `font.family_monospace`

**Label styles**:
- Shapes: `label.style_xcross`, `label.style_cross`, `label.style_circle`, `label.style_square`, `label.style_diamond`, `label.style_triangleup`, `label.style_triangledown`, `label.style_arrowup`, `label.style_arrowdown`, `label.style_flag`
- Labels with pointers: `label.style_label_up`, `label.style_label_down`, `label.style_label_left`, `label.style_label_right`, `label.style_label_upper_left`, `label.style_label_upper_right`, `label.style_label_lower_left`, `label.style_label_lower_right`, `label.style_label_center`
- Text only: `label.style_none`

**Setters**: `label.set_x()`, `label.set_y()`, `label.set_xy()`, `label.set_point()`, `label.set_text()`, `label.set_xloc()`, `label.set_yloc()`, `label.set_color()`, `label.set_style()`, `label.set_textcolor()`, `label.set_size()`, `label.set_textalign()`, `label.set_tooltip()`, `label.set_text_font_family()`, `label.set_text_formatting()`
**Getters**: `label.get_x()`, `label.get_y()`, `label.get_text()`
**Other**: `label.copy()`, `label.delete()`, `label.all`

### polyline.new()

```pinescript
polyline.new(points, curved, closed, xloc, line_color, fill_color,
             line_style, line_width) → series polyline
```

**points**: `array<chart.point>` — up to 10,000 points.
**curved**: `true` = smooth curves between points; `false` = straight segments.
**closed**: `true` = connect last point back to first.
**fill_color**: Fills the enclosed polygon area (only meaningful when `closed = true` or path self-intersects).

**Other**: `polyline.delete()`, `polyline.all`
**No setters** — polylines are immutable after creation. Delete and recreate to modify.

### table.new()

```pinescript
table.new(position, columns, rows, bgcolor, border_color, border_width,
          frame_color, frame_width) → series table
table.cell(table_id, column, row, text, width, height, text_color, text_halign,
           text_valign, text_size, bgcolor, tooltip, text_font_family, text_formatting) → void
```

**position**: `position.top_left`, `position.top_center`, `position.top_right`, `position.middle_left`, `position.middle_center`, `position.middle_right`, `position.bottom_left`, `position.bottom_center`, `position.bottom_right`

**Key behavior**:
- Tables are **pane-anchored** — they stay fixed on screen, do not scroll with chart.
- Tables display **final state only** — only the last update per cell per bar is visible.
- Best practice: update tables on `barstate.islast` only.
- Cannot retrieve table cell properties via getters — store values separately if needed.

**Other**: `table.delete()`, `table.clear()`, `table.set_bgcolor()`, `table.set_border_color()`, `table.set_border_width()`, `table.set_frame_color()`, `table.set_frame_width()`, `table.set_position()`

### linefill.new()

```pinescript
linefill.new(line1, line2, color) → series linefill
```

Fills space between two `line` objects.
- Any pair of lines can have **only one** linefill.
- Successive calls with same line pair **replace** the previous linefill.
- Linefill moves when underlying lines move.

**Setters**: `linefill.set_color()`
**Getters**: `linefill.get_line1()`, `linefill.get_line2()`
**Other**: `linefill.delete()`, `linefill.all`

---

## 5. Fills and Backgrounds

### fill() — Between Plots or Hlines

```pinescript
fill(plot1, plot2, color, title, editable, show_last, fillgaps) → void
fill(hline1, hline2, color, title, editable, fillgaps) → void
```

**Critical**: Cannot mix plot IDs with hline IDs. Both must be same type.
**Color**: Accepts series color — fill color can change per bar.
**Workaround**: To fill between a fixed level and a series, use `plot()` for both (plot the constant as a flat line).

### bgcolor()

```pinescript
bgcolor(color, offset, editable, show_last, title, force_overlay) → void
```

Colors the background of one bar at a time. Use `na` for no color.
**force_overlay**: `true` = color main chart background (even from non-overlay script).
**Gradient pattern**: Combine with `color.from_gradient()` and `ta.percentrank()`.
**Session highlighting**: Use `time(tf, session)` to detect session and apply color.

### barcolor()

```pinescript
barcolor(color, offset, editable, show_last, title, display) → void
```

Colors main chart bars (body, wick, border). Always affects main chart, even from separate pane.
Cannot color bars from `plotbar()`/`plotcandle()`.

---

## 6. Colors

### Color Types

| Qualifier | Description | Color Picker in Settings? |
|-----------|-------------|--------------------------|
| `const color` | Compile-time known (`color.red`, `#FF0000`) | Yes |
| `input color` | User-selectable, not modified by functions | Yes |
| `simple color` | Calculated once at bar 0 | No |
| `series color` | Can change every bar | No |

### Color Functions

```pinescript
color.new(color, transp)           // Apply transparency (0=opaque, 100=invisible)
color.rgb(red, green, blue, transp) // Construct from RGBA (0-255 for RGB, 0-100 for transp)
color.from_gradient(value, bottom_value, top_value, bottom_color, top_color)  // Linear gradient

// Component extraction
color.r(color) → float   // Red (0-255)
color.g(color) → float   // Green (0-255)
color.b(color) → float   // Blue (0-255)
color.t(color) → float   // Transparency (0-100)
```

### Hex Notation

Format: `#RRGGBB` or `#RRGGBBAA`
- AA = alpha channel (reversed: `00` = fully transparent, `FF` = fully opaque)
- Hex `40` ≈ 75% opacity in decimal scale

### 17 Named Colors

`color.aqua`, `color.black`, `color.blue`, `color.fuchsia`, `color.gray`, `color.green`, `color.lime`, `color.maroon`, `color.navy`, `color.olive`, `color.orange`, `color.purple`, `color.red`, `color.silver`, `color.teal`, `color.white`, `color.yellow`

### Conditional Coloring Pattern

```pinescript
// Ternary for dynamic color
color barCol = close > open ? color.green : color.red
barcolor(barCol)

// Gradient based on indicator value
color gradCol = color.from_gradient(rsiValue, 30, 70, color.red, color.green)
bgcolor(gradCol)

// Dynamic transparency
float transp = math.min(80, math.abs(change) * 10)
bgcolor(color.new(color.blue, transp))
```

---

## 7. Horizontal Levels (hline)

```pinescript
hline(price, title, color, linestyle, linewidth, editable, display) → hline
```

**price**: **input int/float only** — cannot use series values.
**color**: **input color only** — cannot change per bar.
**linestyle**: `hline.style_solid`, `hline.style_dotted`, `hline.style_dashed`

Does NOT count toward the 64-plot limit.
Returns `hline` ID for use with `fill()`.

To toggle visibility: set `price` to `na` via input, or use `display` parameter.

---

## 8. Z-Index and Layering (ascending order, bottom to top)

1. Background colors (`bgcolor()`)
2. Fills (`fill()` between plots/hlines)
3. Plots (`plot()`, `plotshape()`, `plotchar()`, `plotarrow()`)
4. Horizontal levels (`hline()`)
5. Linefills (`linefill.new()`)
6. Lines (`line.new()`)
7. Boxes (`box.new()`)
8. Labels (`label.new()`)
9. Tables (`table.new()`)

Enable `explicit_plot_zorder = true` in `indicator()` to control z-order of plot*/hline/fill by script declaration order (later = on top).

**behind_chart parameter**: `indicator(..., behind_chart = true)` renders all script visuals behind chart bars. Default `false` = in front.

---

## 9. Object Limits and Garbage Collection

| Object Type | Default Max | Configurable Max | Parameter |
|------------|------------|-----------------|-----------|
| Lines | 50 | ~500 | `max_lines_count` |
| Boxes | 50 | ~500 | `max_boxes_count` |
| Labels | 50 | ~500 | `max_labels_count` |
| Polylines | 50 | ~100 | `max_polylines_count` |
| Tables | — | No limit documented | — |
| Plots | 64 total | Not configurable | — |

**Garbage collection**: When limit is reached, the **oldest** object is automatically deleted. This is silent — no error, no warning.

**Prevention pattern**: Manually delete old objects before creating new ones:
```pinescript
// Using *.all array
if array.size(line.all) >= max_lines_count
    line.delete(array.first(line.all))
```

**Polyline points**: Up to 10,000 `chart.point` objects per polyline.

---

## 10. Display Parameter

Controls where visual output appears:

| Value | Description |
|-------|-------------|
| `display.all` | All outputs (default) |
| `display.pane` | Chart pane only |
| `display.status_line` | Indicator status line only |
| `display.data_window` | Data Window only |
| `display.price_scale` | Price scale only |
| `display.none` | Hidden everywhere |

Combine with `+` (add) and `-` (subtract):
```pinescript
plot(close, display = display.all - display.status_line)  // everywhere except status line
plot(value, display = display.data_window + display.pane)  // data window and pane only
```

---

## 11. UI Drawing Tools vs Pine Script Drawings

**Important distinction**: TradingView's left sidebar drawing tools (trend lines, horizontal lines, text, rectangles, patterns, projections, rulers, etc.) are **manual UI drawings** — they are NOT Pine Script objects and cannot be created, read, modified, or detected by Pine Script code.

Pine Script can only create drawings via its own functions (`line.new()`, `box.new()`, `label.new()`, `polyline.new()`, `table.new()`). These are separate from manual UI drawings and appear in a different layer.

**Implications for automation (TTE)**:
- Selenium/browser automation CAN interact with UI drawing tools (clicking buttons, placing drawings)
- Pine Script indicators draw programmatically via code only
- Both types of drawings appear on chart snapshots

---

## 12. Common Patterns and Gotchas

### Drawing at Historical Time vs Current Bar

**Problem**: When using `xloc.bar_time` with a historical timestamp, the drawing renders at that historical position. If the chart is scrolled to show current bars, the drawing may be off-screen (too far left).

```pinescript
// Drawing at historical time — may be off-screen if timestamp is old
line.new(historicalTimestamp, price, historicalTimestamp + duration, price, xloc.bar_time)

// Drawing near current bar — always visible
int dt = time - time[1]
line.new(time - 5 * dt, price, time + 25 * dt, price, xloc.bar_time)
```

**When this matters**: Snapshot tools that take screenshots of the current chart view. If drawings are anchored at old timestamps, they won't appear in the snapshot.

### Persistent Drawing Pattern (Delete + Recreate on Last Bar)

```pinescript
var line myLine = na

if barstate.islast
    line.delete(myLine)
    myLine := line.new(bar_index - 10, close, bar_index + 10, close)
```

This pattern ensures only one instance exists, updated every tick on the last bar.

### Conditional Drawing (Only When Inputs Are Valid)

```pinescript
bool hasValidInputs = entry != 0 and sl != 0 and tp1 != 0

if barstate.islast and hasValidInputs
    // Create drawings only when meaningful data exists
```

### Vertical Lines via line.new()

```pinescript
// Both x-coordinates same, different y-values
line.new(bar_index, low - atr, bar_index, high + atr, color = color.gray)
```

### Future Positioning

```pinescript
// bar_index method — up to 500 bars forward
label.new(bar_index + 20, close, "Future")

// time method — any future time (but bars may not exist)
label.new(time + 86400000, close, "Tomorrow", xloc = xloc.bar_time)
```

### Efficient Last-Bar Label Update

```pinescript
var label lbl = na
if barstate.islast
    if na(lbl)
        lbl := label.new(bar_index, close, "")
    label.set_xy(lbl, bar_index, close)
    label.set_text(lbl, "Price: " + str.tostring(close, format.mintick))
```

### Creating Gaps in Plots

Use `na` values with `plot.style_linebr`:
```pinescript
plot(condition ? value : na, style = plot.style_linebr)
```

### Fill Between Plot and Constant Level

Cannot mix `plot()` and `hline()` in `fill()`. Use two plots instead:
```pinescript
p1 = plot(series)
p2 = plot(constantLevel)  // use plot() not hline()
fill(p1, p2, color = color.new(color.blue, 80))
```

---

## 13. Trade Drawer Pattern (TTE Project)

The TTE Trade Drawer indicator (`Pine Script Code/Trade Drawer.txt`) demonstrates a complete drawing pattern for visualizing trade levels:

**Architecture**:
- Draws entry, SL, TP1/TP2/TP3 horizontal lines with linefill zones
- Uses `xloc.bar_time` for time-based positioning
- Deletes and recreates all objects on `barstate.islast`
- Inputs populated by TTE Python automation via `change_settings()`

**Key design decisions**:
- `max_lines_count = 10`, `max_labels_count = 10` (small, known quantity)
- `var` declarations for all drawing objects (persist across ticks)
- Lines span from `startTime` to `startTime + 30*dt` (30 bars duration)
- Labels at end of lines with `label.style_none` for clean text-only display
- Linefill between entry-SL (orange/risk) and entry-TP (blue/profit) zones

**Snapshot visibility consideration**:
When `dateTime` (entry timestamp) is far in the past, the lines render off-screen to the left. For snapshot use, anchor drawings near the current bar instead:
```pinescript
int dt = time - time[1]
int startTime = time - 5 * dt    // 5 bars before current
int endTime = time + 25 * dt     // 25 bars into right margin
```
