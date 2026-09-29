/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.components;

import java.awt.BasicStroke;
import java.awt.Color;
import java.awt.Dimension;
import java.awt.FontMetrics;
import java.awt.Graphics;
import java.awt.Graphics2D;
import java.awt.Point;
import java.awt.Rectangle;
import java.awt.RenderingHints;
import java.awt.Shape;
import java.awt.event.MouseAdapter;
import java.awt.event.MouseEvent;
import javax.swing.JComponent;
import javax.swing.event.ChangeEvent;
import javax.swing.event.ChangeListener;
import javax.swing.event.EventListenerList;

/**
 * Two-thumb slider specialized for SNES bank range selection.
 *
 * <p>The component uses an inclusive bank range and enforces a forbidden interval
 * ({@code $40-$7F}) that thumbs cannot select directly.
 */
public final class SystemBankRangeSlider extends JComponent {
  private static final int PREF_WIDTH = 700;
  private static final int PREF_HEIGHT = 58;
  private static final double FORBIDDEN_VISUAL_SCALE = 0.30;

  private static final int HORIZONTAL_PADDING = 24;
  private static final int TOP_PADDING = 10;
  private static final int TRACK_HEIGHT = 10;
  private static final int THUMB_RADIUS = 11;
  private static final int LABEL_GAP = 10;

  private static final Color TRACK_COLOR = new Color(152, 158, 170);
  private static final Color ACTIVE_COLOR = new Color(55, 97, 194);
  private static final Color FORBIDDEN_BG = new Color(255, 240, 240);
  private static final Color FORBIDDEN_HATCH = new Color(220, 80, 80);
  private static final Color THUMB_FILL = new Color(245, 245, 245);
  private static final Color THUMB_BORDER = new Color(85, 90, 100);
  private static final Color TICK_COLOR = new Color(90, 90, 90);
  private static final Color LABEL_COLOR = new Color(60, 60, 60);

  private static final int HATCH_STEP = 8;

  private final int minBank;
  private final int maxBank;
  private final int forbiddenMin;
  private final int forbiddenMax;

  private final EventListenerList listenerList = new EventListenerList();

  private int startBank;
  private int endBank;
  private int lastPointerBank;
  private Thumb activeThumb = Thumb.NONE;

  /**
   * Creates the dual-thumb slider.
   *
   * @param minBank inclusive minimum selectable bank
   * @param maxBank inclusive maximum selectable bank
   * @param forbiddenMin inclusive start of forbidden interval
   * @param forbiddenMax inclusive end of forbidden interval
   * @param startBank initial start bank
   * @param endBank initial end bank
   */
  public SystemBankRangeSlider(
      int minBank,
      int maxBank,
      int forbiddenMin,
      int forbiddenMax,
      int startBank,
      int endBank) {
    this.minBank = minBank;
    this.maxBank = maxBank;
    this.forbiddenMin = forbiddenMin;
    this.forbiddenMax = forbiddenMax;

    setRange(startBank, endBank);
    installMouseHandlers();
  }

  @Override
  public Dimension getPreferredSize() {
    return new Dimension(PREF_WIDTH, PREF_HEIGHT);
  }

  /**
   * Adds a listener that will be notified when either thumb value changes.
   *
   * @param listener listener to register
   */
  public void addChangeListener(ChangeListener listener) {
    listenerList.add(ChangeListener.class, listener);
  }

  /**
   * Removes a previously registered change listener.
   *
   * @param listener listener to unregister
   */
  public void removeChangeListener(ChangeListener listener) {
    listenerList.remove(ChangeListener.class, listener);
  }

  /**
   * Returns the current inclusive start bank.
   */
  public int getStartBank() {
    return startBank;
  }

  /**
   * Returns the current inclusive end bank.
   */
  public int getEndBank() {
    return endBank;
  }

  /**
   * Sets the current inclusive range and refreshes component state.
   *
   * @param startBank inclusive start bank
   * @param endBank inclusive end bank
   */
  public void setRange(int startBank, int endBank) {
    int normalizedStart = normalizeBank(startBank, Thumb.START);
    int normalizedEnd = normalizeBank(endBank, Thumb.END);

    if (normalizedStart > normalizedEnd) {
      int temp = normalizedStart;
      normalizedStart = normalizedEnd;
      normalizedEnd = temp;
    }

    boolean changed = this.startBank != normalizedStart || this.endBank != normalizedEnd;
    this.startBank = normalizedStart;
    this.endBank = normalizedEnd;
    this.lastPointerBank = normalizedStart;

    repaint();
    if (changed) {
      fireStateChanged();
    }
  }

  @Override
  protected void paintComponent(Graphics graphics) {
    super.paintComponent(graphics);

    Graphics2D g2 = (Graphics2D) graphics.create();
    g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);

    Rectangle track = getTrackBounds();
    paintTrack(g2, track);
    paintSelection(g2, track);
    paintForbiddenRange(g2, track);
    paintTicksAndLabels(g2, track);
    paintThumb(g2, track, startBank);
    paintThumb(g2, track, endBank);

    g2.dispose();
  }

  private void installMouseHandlers() {
    MouseAdapter mouseAdapter =
        new MouseAdapter() {
          @Override
          public void mousePressed(MouseEvent event) {
            if (!isEnabled()) {
              return;
            }

            Point point = event.getPoint();
            activeThumb = selectActiveThumb(point.x);
            lastPointerBank = bankFromX(point.x);
            updateActiveThumb(point.x);
          }

          @Override
          public void mouseDragged(MouseEvent event) {
            if (!isEnabled() || activeThumb == Thumb.NONE) {
              return;
            }

            updateActiveThumb(event.getX());
          }

          @Override
          public void mouseReleased(MouseEvent event) {
            activeThumb = Thumb.NONE;
          }
        };

    addMouseListener(mouseAdapter);
    addMouseMotionListener(mouseAdapter);
  }

  private void updateActiveThumb(int mouseX) {
    int candidate = bankFromX(mouseX);
    int nextStart = startBank;
    int nextEnd = endBank;

    if (activeThumb == Thumb.START) {
      nextStart = normalizeBank(candidate, Thumb.START);
      nextStart = Math.min(nextStart, endBank);
    } else if (activeThumb == Thumb.END) {
      nextEnd = normalizeBank(candidate, Thumb.END);
      nextEnd = Math.max(nextEnd, startBank);
    }

    boolean changed = nextStart != startBank || nextEnd != endBank;
    startBank = nextStart;
    endBank = nextEnd;
    lastPointerBank = candidate;

    repaint();
    if (changed) {
      fireStateChanged();
    }
  }

  private Thumb selectActiveThumb(int mouseX) {
    Rectangle track = getTrackBounds();
    int startX = bankToX(startBank, track);
    int endX = bankToX(endBank, track);

    int startDistance = Math.abs(mouseX - startX);
    int endDistance = Math.abs(mouseX - endX);

    if (startDistance == endDistance) {
      return mouseX <= (startX + endX) / 2 ? Thumb.START : Thumb.END;
    }
    return startDistance < endDistance ? Thumb.START : Thumb.END;
  }

  private void paintTrack(Graphics2D g2, Rectangle track) {
    g2.setColor(TRACK_COLOR);
    g2.fillRoundRect(track.x, track.y, track.width, track.height, TRACK_HEIGHT, TRACK_HEIGHT);
  }

  private void paintSelection(Graphics2D g2, Rectangle track) {
    paintSelectionSegment(g2, track, startBank, endBank, minBank, forbiddenMin - 1, true, false);
    paintSelectionSegment(g2, track, startBank, endBank, forbiddenMax + 1, maxBank, false, true);
  }

  private void paintSelectionSegment(
      Graphics2D g2,
      Rectangle track,
      int start,
      int end,
      int segmentStart,
      int segmentEnd,
      boolean canRoundStart,
      boolean canRoundEnd) {
    int visibleStart = Math.max(start, segmentStart);
    int visibleEnd = Math.min(end, segmentEnd);
    if (visibleStart > visibleEnd) {
      return;
    }

    int x1 = bankToX(visibleStart, track);
    int x2 = bankToX(Math.min(visibleEnd + 1, maxBank + 1), track);
    int width = Math.max(1, x2 - x1);

    g2.setColor(ACTIVE_COLOR);
    boolean roundStart = canRoundStart && visibleStart == segmentStart;
    boolean roundEnd = canRoundEnd && visibleEnd == segmentEnd;

    if (!roundStart && !roundEnd) {
      g2.fillRect(x1, track.y, width, track.height);
      return;
    }

    g2.fillRoundRect(x1, track.y, width, track.height, TRACK_HEIGHT, TRACK_HEIGHT);

    int capWidth = Math.min(Math.max(1, TRACK_HEIGHT / 2), width);
    if (!roundStart) {
      g2.fillRect(x1, track.y, capWidth, track.height);
    }
    if (!roundEnd) {
      g2.fillRect(x1 + width - capWidth, track.y, capWidth, track.height);
    }
  }

  private void paintForbiddenRange(Graphics2D g2, Rectangle track) {
    int x1 = bankToX(forbiddenMin, track);
    int x2 = bankToX(forbiddenMax + 1, track);
    int width = Math.max(1, x2 - x1);

    Shape previousClip = g2.getClip();
    g2.clipRect(x1, track.y, width, track.height);

    g2.setColor(FORBIDDEN_BG);
    g2.fillRect(x1, track.y, width, track.height);

    g2.setColor(FORBIDDEN_HATCH);
    g2.setStroke(new BasicStroke(1.5f));
    for (int hatchX = x1 - track.height; hatchX < x2 + track.height; hatchX += HATCH_STEP) {
      g2.drawLine(hatchX, track.y + track.height, hatchX + track.height, track.y);
    }

    g2.setClip(previousClip);
  }

  private void paintTicksAndLabels(Graphics2D g2, Rectangle track) {
    g2.setColor(TICK_COLOR);

    paintTickLabel(g2, track, 0x00, "00");
    paintTickLabel(g2, track, 0x40, "40");
    paintTickLabel(g2, track, 0x80, "80");
    paintTickLabel(g2, track, 0xbf, "BF");
  }

  private void paintTickLabel(Graphics2D g2, Rectangle track, int bank, String label) {
    int x = bankToX(bank, track);
    int tickTop = track.y + track.height + 2;
    int tickBottom = tickTop + 8;

    g2.drawLine(x, tickTop, x, tickBottom);

    FontMetrics metrics = g2.getFontMetrics();
    int labelX = x - (metrics.stringWidth(label) / 2);
    int labelY = tickBottom + LABEL_GAP;

    g2.setColor(LABEL_COLOR);
    g2.drawString(label, labelX, labelY);
    g2.setColor(TICK_COLOR);
  }

  private void paintThumb(Graphics2D g2, Rectangle track, int bank) {
    int x = bankToX(bank, track);
    int y = track.y + (track.height / 2);

    g2.setColor(THUMB_FILL);
    g2.fillOval(x - THUMB_RADIUS, y - THUMB_RADIUS, THUMB_RADIUS * 2, THUMB_RADIUS * 2);

    g2.setColor(THUMB_BORDER);
    g2.setStroke(new BasicStroke(1.3f));
    g2.drawOval(x - THUMB_RADIUS, y - THUMB_RADIUS, THUMB_RADIUS * 2, THUMB_RADIUS * 2);
  }

  private Rectangle getTrackBounds() {
    int width = Math.max(1, getWidth() - (HORIZONTAL_PADDING * 2));
    return new Rectangle(HORIZONTAL_PADDING, TOP_PADDING, width, TRACK_HEIGHT);
  }

  private int bankToX(int bank, Rectangle track) {
    TrackLayout layout = computeTrackLayout(track);
    int bankPoint = Math.max(minBank, Math.min(maxBank + 1, bank));

    int leftRange = forbiddenMin - minBank;
    if (bankPoint <= forbiddenMin) {
      return interpolate(layout.startX, layout.leftEndX, bankPoint - minBank, leftRange);
    }

    int middleStart = forbiddenMin;
    int middleEnd = forbiddenMax + 1;
    int middleRange = middleEnd - middleStart;
    if (bankPoint <= middleEnd) {
      return interpolate(layout.leftEndX, layout.middleEndX, bankPoint - middleStart, middleRange);
    }

    int rightStart = forbiddenMax + 1;
    int rightRange = maxBank - rightStart;
    return interpolate(layout.middleEndX, layout.endX, bankPoint - rightStart, rightRange);
  }

  private int bankFromX(int x) {
    Rectangle track = getTrackBounds();
    TrackLayout layout = computeTrackLayout(track);
    int clampedX = Math.max(layout.startX, Math.min(layout.endX, x));

    int bank;
    if (clampedX <= layout.leftEndX) {
      int leftRange = forbiddenMin - minBank;
      bank = minBank + interpolateValue(layout.startX, layout.leftEndX, clampedX, leftRange);
    } else if (clampedX <= layout.middleEndX) {
      int middleRange = (forbiddenMax + 1) - forbiddenMin;
      bank = forbiddenMin +
        interpolateValue(layout.leftEndX, layout.middleEndX, clampedX, middleRange);
    } else {
      int rightStart = forbiddenMax + 1;
      int rightRange = maxBank - rightStart;
      bank = rightStart + interpolateValue(layout.middleEndX, layout.endX, clampedX, rightRange);
    }

    return clamp(bank);
  }

  private TrackLayout computeTrackLayout(Rectangle track) {
    int leftSpan = Math.max(1, forbiddenMin - minBank);
    int middleSpan = Math.max(1, (forbiddenMax + 1) - forbiddenMin);
    int rightSpan = Math.max(1, maxBank - (forbiddenMax + 1));

    double leftWeight = leftSpan;
    double middleWeight = middleSpan * FORBIDDEN_VISUAL_SCALE;
    double rightWeight = rightSpan;
    double totalWeight = leftWeight + middleWeight + rightWeight;

    int leftWidth = Math.max(1, (int) Math.round(track.width * (leftWeight / totalWeight)));
    int middleWidth = Math.max(1, (int) Math.round(track.width * (middleWeight / totalWeight)));
    int rightWidth = track.width - leftWidth - middleWidth;

    if (rightWidth < 1) {
      rightWidth = 1;
      middleWidth = Math.max(1, track.width - leftWidth - rightWidth);
      if (leftWidth + middleWidth + rightWidth > track.width) {
        leftWidth = Math.max(1, track.width - middleWidth - rightWidth);
      }
    }

    int startX = track.x;
    int leftEndX = startX + leftWidth;
    int middleEndX = leftEndX + middleWidth;
    int endX = track.x + track.width;
    return new TrackLayout(startX, leftEndX, middleEndX, endX);
  }

  private static int interpolate(
      int fromX,
      int toX,
      int valueWithinSegment,
      int segmentRange) {
    if (segmentRange <= 0 || fromX == toX) {
      return toX;
    }
    double ratio = valueWithinSegment / (double) segmentRange;
    return fromX + (int) Math.round(ratio * (toX - fromX));
  }

  private static int interpolateValue(
      int fromX,
      int toX,
      int x,
      int segmentRange) {
    int width = toX - fromX;
    if (segmentRange <= 0 || width <= 0) {
      return segmentRange;
    }
    double ratio = (x - fromX) / (double) width;
    return (int) Math.round(ratio * segmentRange);
  }

  private int normalizeBank(int bank, Thumb thumb) {
    int clamped = clamp(bank);
    if (!isForbidden(clamped)) {
      return clamped;
    }

    int lower = forbiddenMin - 1;
    int upper = forbiddenMax + 1;

    if (lastPointerBank < forbiddenMin) {
      return lower;
    }
    if (lastPointerBank > forbiddenMax) {
      return upper;
    }

    int distanceToLower = Math.abs(clamped - lower);
    int distanceToUpper = Math.abs(clamped - upper);
    if (distanceToLower == distanceToUpper) {
      return thumb == Thumb.START ? lower : upper;
    }
    return distanceToLower < distanceToUpper ? lower : upper;
  }

  private boolean isForbidden(int bank) {
    return bank >= forbiddenMin && bank <= forbiddenMax;
  }

  private int clamp(int bank) {
    return Math.max(minBank, Math.min(maxBank, bank));
  }

  private void fireStateChanged() {
    ChangeEvent event = new ChangeEvent(this);
    for (ChangeListener listener : listenerList.getListeners(ChangeListener.class)) {
      listener.stateChanged(event);
    }
  }

  private enum Thumb {
    NONE,
    START,
    END
  }

  private static final class TrackLayout {
    private final int startX;
    private final int leftEndX;
    private final int middleEndX;
    private final int endX;

    private TrackLayout(int startX, int leftEndX, int middleEndX, int endX) {
      this.startX = startX;
      this.leftEndX = leftEndX;
      this.middleEndX = middleEndX;
      this.endX = endX;
    }
  }
}
