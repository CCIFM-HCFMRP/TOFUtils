cmake_minimum_required(VERSION 3.5)

project(TOFFUtils)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/TOFF_Utils")
set(EXTENSION_CATEGORY "FMRP")
set(EXTENSION_CONTRIBUTORS "Julio C Ferranti (CCIFM-FMRP-USP)")
set(EXTENSION_DESCRIPTION "Utilitarios TOF")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/TOFFUtils.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/TOFFUtils/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(TOFDiff)
add_subdirectory(TOFVol)
add_subdirectory(TOFView)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
