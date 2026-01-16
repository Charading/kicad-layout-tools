# Main unified plugin with tabs
from .layout_tools_main import LayoutToolsPlugin

# Individual plugins (kept for backward compatibility, but not registered by default)
# Uncomment the lines below if you want separate buttons instead of the tabbed interface
# from .rotate_individually import RotateIndividuallyPlugin
# from .chain_route import ChainRouteLEDsPlugin
# RotateIndividuallyPlugin().register()
# ChainRouteLEDsPlugin().register()

# Register the main tabbed plugin
LayoutToolsPlugin().register()
