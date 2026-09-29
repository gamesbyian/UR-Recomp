/* (C) Arnaud 'red' Rouyer 2026 */
package ghidra_snes.ui.options;

import docking.widgets.tree.GTree;
import ghidra.program.model.listing.Program;
import ghidra.util.Swing;
import ghidra_snes.ui.components.OptionsTreeNode;
import ghidra_snes.ui.options.pages.MemoryMapPage;
import ghidra_snes.ui.options.pages.RomDetailsPage;
import ghidra_snes.ui.options.pages.RomMirrorsPage;
import ghidra_snes.ui.options.pages.SystemBanksPage;
import java.awt.BorderLayout;
import java.awt.CardLayout;
import javax.swing.JPanel;
import javax.swing.JSplitPane;
import javax.swing.event.TreeExpansionEvent;
import javax.swing.event.TreeExpansionListener;
import javax.swing.tree.TreePath;
import javax.swing.tree.TreeSelectionModel;

public final class SnesOptionsComponent extends JPanel {
  private static final String ROM_DETAILS_PAGE = "/";
  private static final String MEMORY_MAP_PAGE = "/memory/";
  private static final String SYSTEM_BANKS_PAGE = "/memory/system_banks";
  private static final String ROM_MIRRORS_PAGE = "/memory/rom_mirrors";

  private final CardLayout pageLayout = new CardLayout();
  private final JPanel pagePanel = new JPanel(pageLayout);

  /**
   * Creates the base options component containing the tree navigation and page area.
   *
   * @param currentProgram active program used to initialize ROM-dependent pages
   */
  public SnesOptionsComponent(Program currentProgram) {
    super(new BorderLayout());

    GTree tree = buildTree();
    registerPages(currentProgram);

    JSplitPane splitPane = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT, tree, pagePanel);
    splitPane.setResizeWeight(0.0);
    splitPane.setDividerLocation(280);
    splitPane.setDividerSize(6);
    splitPane.setOneTouchExpandable(true);

    add(splitPane, BorderLayout.CENTER);
  }

  /**
   * Registers all available option pages in the right-side card layout.
   *
   * @param currentProgram active program passed to the ROM details page
   */
  private void registerPages(Program currentProgram) {
    pagePanel.add(new RomDetailsPage(currentProgram), ROM_DETAILS_PAGE);
    pagePanel.add(new MemoryMapPage(), MEMORY_MAP_PAGE);
    pagePanel.add(new SystemBanksPage(currentProgram), SYSTEM_BANKS_PAGE);
    pagePanel.add(new RomMirrorsPage(currentProgram), ROM_MIRRORS_PAGE);
  }

  /**
   * Builds the left navigation tree and wires selection/expansion behavior.
   *
   * @return configured options tree
   */
  private GTree buildTree() {
    OptionsTreeNode rootNode = OptionsTreeNode.folder("SNES Options", null, false);
    OptionsTreeNode romDetailsNode =
      OptionsTreeNode.leaf("ROM Details", ROM_DETAILS_PAGE);
    OptionsTreeNode memoryMapNode =
      OptionsTreeNode.folder("Memory Map", MEMORY_MAP_PAGE, false);
    OptionsTreeNode systemBanksNode =
      OptionsTreeNode.leaf("System Banks", SYSTEM_BANKS_PAGE);
    OptionsTreeNode romMirrorsNode =
      OptionsTreeNode.leaf("ROM Mirrors", ROM_MIRRORS_PAGE);

    rootNode.addChild(romDetailsNode);
    rootNode.addChild(memoryMapNode);
    memoryMapNode.addChild(systemBanksNode);
    memoryMapNode.addChild(romMirrorsNode);

    GTree tree = new GTree(rootNode);
    tree.setRootVisible(false);
    tree.setShowsRootHandles(true);
    tree.setRootNodeAllowedToCollapse(false);
    tree.getSelectionModel().setSelectionMode(TreeSelectionModel.SINGLE_TREE_SELECTION);
    tree.expandPath(memoryMapNode);
    tree.addGTreeSelectionListener(event -> showSelectedPage(tree));
    tree.addTreeExpansionListener(createExpansionListener(tree));
    tree.setSelectedNode(romDetailsNode);
    return tree;
  }

  /**
   * Creates a listener that immediately re-expands non-collapsible folder nodes.
   *
   * @param tree owning tree instance
   * @return expansion listener enforcing folder visibility rules
   */
  private TreeExpansionListener createExpansionListener(GTree tree) {
    return new TreeExpansionListener() {
      @Override
      public void treeExpanded(TreeExpansionEvent event) {
        // no-op
      }

      @Override
      public void treeCollapsed(TreeExpansionEvent event) {
        Object node = event.getPath().getLastPathComponent();
        if (!(node instanceof OptionsTreeNode optionsNode)) {
          return;
        }
        if (optionsNode.isCollapsible()) {
          return;
        }

        TreePath collapsedPath = event.getPath();
        Swing.runLater(() -> tree.expandPath(collapsedPath));
      }
    };
  }

  /**
   * Switches the right panel to the page mapped by the currently selected tree node.
   * Falls back to ROM Details when the selection is missing or invalid.
   *
   * @param tree source tree holding the active selection
   */
  private void showSelectedPage(GTree tree) {
    TreePath selectionPath = tree.getSelectionPath();
    if (selectionPath == null) {
      pageLayout.show(pagePanel, ROM_DETAILS_PAGE);
      return;
    }

    Object selectedNode = selectionPath.getLastPathComponent();
    if (!(selectedNode instanceof OptionsTreeNode optionsNode)) {
      pageLayout.show(pagePanel, ROM_DETAILS_PAGE);
      return;
    }

    String pageKey = optionsNode.getPageKey();
    if (pageKey == null) {
      pageLayout.show(pagePanel, ROM_DETAILS_PAGE);
      return;
    }

    pageLayout.show(pagePanel, pageKey);
  }
}
