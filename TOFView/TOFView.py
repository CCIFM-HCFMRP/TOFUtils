import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

#
# TOFView
#

class TOFView(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "TOFView"
    self.parent.categories = ["HCFMRP"]
    self.parent.dependencies = []
    self.parent.contributors = ["Julio C Ferranti (CCIFM-HCRP-USP)"]
    self.parent.helpText = """ """
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """ """

# TOFViewWidget
class TOFViewWidget(ScriptedLoadableModuleWidget):
    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...
        # Parameters Area
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parametros"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # input volume selector
        self.baseSelector = slicer.qMRMLNodeComboBox()
        self.baseSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.baseSelector.selectNodeUponCreation = False
        self.baseSelector.addEnabled = False
        self.baseSelector.removeEnabled = False
        self.baseSelector.noneEnabled = False
        self.baseSelector.showHidden = False
        self.baseSelector.showChildNodeTypes = False
        self.baseSelector.setMRMLScene( slicer.mrmlScene )
        self.baseSelector.setToolTip( "Volume base para comparacao" )
        parametersFormLayout.addRow("Volume Base: ", self.baseSelector)

        # label 1 volume selector
        self.label1Selector = slicer.qMRMLNodeComboBox()
        self.label1Selector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.label1Selector.selectNodeUponCreation = True
        self.label1Selector.addEnabled = False
        self.label1Selector.removeEnabled = False
        self.label1Selector.noneEnabled = True
        self.label1Selector.showHidden = False
        self.label1Selector.showChildNodeTypes = False
        self.label1Selector.setMRMLScene( slicer.mrmlScene )
        parametersFormLayout.addRow("Label Map 1: ", self.label1Selector)

        self.label1Model = qt.QLabel()
        self.label1Model.enabled = False
        parametersFormLayout.addRow("Model:", self.label1Model)

        # label 2 volume selector
        self.label2Selector = slicer.qMRMLNodeComboBox()
        self.label2Selector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.label2Selector.selectNodeUponCreation = True
        self.label2Selector.addEnabled = False
        self.label2Selector.removeEnabled = False
        self.label2Selector.noneEnabled = True
        self.label2Selector.showHidden = False
        self.label2Selector.showChildNodeTypes = False
        self.label2Selector.setMRMLScene( slicer.mrmlScene )
        parametersFormLayout.addRow("Label Map 2: ", self.label2Selector)

        self.label2Model = qt.QLabel()
        self.label2Model.enabled = False
        parametersFormLayout.addRow("Model:", self.label2Model)

        # threshold value
        self.sliderWidget = ctk.ctkSliderWidget()
        self.sliderWidget.singleStep = 0.1
        self.sliderWidget.minimum = 0
        self.sliderWidget.maximum = 1
        self.sliderWidget.value = 0.5
        self.sliderWidget.enabled = False
        parametersFormLayout.addRow("label 2 <-> Label 1", self.sliderWidget)

        # Add vertical spacer
        self.layout.addStretch(1)

        # connections
        self.sliderWidget.connect("valueChanged(double)", self.onValueChanged)
        self.baseSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.baseSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.transparencyOnSelect)
        self.baseSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.setBackground)
        self.label1Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.transparencyOnSelect)
        self.label1Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.setLabel1)
        self.label2Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.transparencyOnSelect)
        self.label2Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.setLabel2)

        # Refresh Apply button state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.sliderWidget.enabled = True
        pass

    def setBackground(self):
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.baseSelector.currentNode().GetID())

    def setLabel1(self):
        for node in slicer.util.getNodesByClass('vtkMRMLModelNode'):
            if self.label1Selector.currentNode().GetName() in node.GetName():
                self.label1Model.text = node.GetName()
                self.label1DisplayNode = node.GetModelDisplayNode()
                self.label1DisplayNode.SetOpacity(0.5)
                for color in ['Red', 'Yellow', 'Green']:
                    slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetForegroundVolumeID(self.label1Selector.currentNode().GetID())
                    slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetForegroundOpacity(0.5)
                return

    def setLabel2(self):
        for node in slicer.util.getNodesByClass('vtkMRMLModelNode'):
            if self.label2Selector.currentNode().GetName() in node.GetName():
                self.label2Model.text = node.GetName()
                self.label2DisplayNode = node.GetModelDisplayNode()
                self.label2DisplayNode.SetOpacity(0.5)
                for color in ['Red', 'Yellow', 'Green']:
                    slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(self.label2Selector.currentNode().GetID())
                    slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelOpacity(0.5)
                return

    def transparencyOnSelect(self):
        self.sliderWidget.enabled = self.baseSelector.currentNode() and self.label1Selector.currentNode() and self.label2Selector.currentNode()
        if self.label1Selector.currentNode() and self.label2Selector.currentNode():
            if self.label1Selector.currentNode().GetID() == self.label2Selector.currentNode().GetID():
                logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
                slicer.util.errorDisplay('Label Maps iguais. Por favor escolha outro.')

        for node in slicer.util.getNodesByClass('vtkMRMLModelNode'):
            if node.GetName()!=self.label1Selector.currentNode().GetName() or node.GetName()!=self.label2Selector.currentNode().GetName():
                node.GetModelDisplayNode().SetOpacity(0)
            else:
                node.GetModelDisplayNode().SetOpacity(0.5)

    def onValueChanged(self):
        if not self.isValidInputOutputData(self.label1Selector.currentNode(), self.label2Selector.currentNode()):
            slicer.util.errorDisplay('Label Maps iguais. Por favor mude um dos labels.')
            return False

        #codigo para transparencia
        highValue = self.sliderWidget.value
        lowValue = 1 - self.sliderWidget.value
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetForegroundOpacity(highValue)
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelOpacity(lowValue)

        self.label1DisplayNode.SetOpacity(highValue)
        self.label2DisplayNode.SetOpacity(lowValue)

        return

    def hasImageData(self,volumeNode):
        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def isValidInputOutputData(self, volume1, volume2):
        if not volume1:
            logging.debug('isValidInputOutputData failed: no input volume node defined')
            return False
        if not volume2:
            logging.debug('isValidInputOutputData failed: no output volume node defined')
            return False
        if volume1.GetID()==volume2.GetID():
            logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True
