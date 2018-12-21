import os
import unittest
import vtk, qt, ctk, numpy, slicer
from slicer.ScriptedLoadableModule import *
import logging

# TOFDiff
class TOFDiff(ScriptedLoadableModule):
  "Uses ScriptedLoadableModule base class, available at: https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py"

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "TOF Diff"
    self.parent.categories = ["HCFMRP"]
    self.parent.dependencies = []
    self.parent.contributors = ["Julio Cesar Ferranti (CCIFM-HCRP-FMRP-USP)"]
    self.parent.helpText = "Faz a diferenca entre duas sequencias TOF"
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = ""

# TOFDiffWidget
class TOFDiffWidget(ScriptedLoadableModuleWidget):

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...

        # Parameters Area
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # Seletor do primeiro volume TOF
        self.firstSelector = slicer.qMRMLNodeComboBox()
        self.firstSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.firstSelector.selectNodeUponCreation = True
        self.firstSelector.addEnabled = False
        self.firstSelector.removeEnabled = False
        self.firstSelector.noneEnabled = False
        self.firstSelector.showHidden = False
        self.firstSelector.showChildNodeTypes = False
        self.firstSelector.setMRMLScene( slicer.mrmlScene )
        self.firstSelector.setToolTip("Insira o exame mais antigo.")
        parametersFormLayout.addRow("Primeiro exame: ", self.firstSelector)

        # Seletor da ROI (LabelMap)
        self.ROISelector = slicer.qMRMLNodeComboBox()
        self.ROISelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.ROISelector.selectNodeUponCreation = True
        self.ROISelector.addEnabled = False
        self.ROISelector.removeEnabled = False
        self.ROISelector.noneEnabled = True
        self.ROISelector.showHidden = False
        self.ROISelector.showChildNodeTypes = False
        self.ROISelector.setMRMLScene( slicer.mrmlScene )
        self.ROISelector.setToolTip("Insira A ROI.")
        parametersFormLayout.addRow("ROI: ", self.ROISelector)

        # Apply Button
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.enabled = False
        parametersFormLayout.addRow(self.applyButton)

        # Progress Bar
        self.progressBar = qt.QProgressBar()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(0)
        self.progressBar.setVisible(False)
        parametersFormLayout.addRow(self.progressBar)

        # Add vertical spacer
        self.layout.addStretch(1)

        # connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)
        self.firstSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.ROISelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

        # Refresh Apply button state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.firstSelector.currentNode()

    def onApplyButton(self):
        self.applyButton.setText("Aguarde...")
        self.applyButton.setEnabled(False)
        self.progressBar.setVisible(True)
        slicer.app.processEvents()

        logic = TOFDiffLogic()
        logic.run(self.firstSelector.currentNode(), self.ROISelector.currentNode())

        self.applyButton.setText("Iniciar")
        self.applyButton.setEnabled(True)
        self.progressBar.setVisible(False)

# TOFDiffLogic
class TOFDiffLogic(ScriptedLoadableModuleLogic):
    def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
        "Validates if the output is not the same as input"
        if not inputVolumeNode:
            logging.debug('isValidInputOutputData failed: no input volume node defined')
            return False
        if not outputVolumeNode:
            logging.debug('isValidInputOutputData failed: no output volume node defined')
            return False
        if inputVolumeNode.GetID()==outputVolumeNode.GetID():
            logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True

    def mean(self, inputVolume, ROIVolume):
        "Executa a calculo da media dos volumes com a ROI"

        logging.info('Processing mean: ' + inputVolume.GetName())

        if not self.isValidInputOutputData(inputVolume, ROIVolume):
            slicer.util.errorDisplay('Mean: Input volume is the same as output volume. Choose a different output volume.')
            return False

        stataccum = vtk.vtkImageAccumulate()
        stataccum.SetInputConnection(ROIVolume.GetImageDataConnection())
        stataccum.Update()
        lo = int(stataccum.GetMin()[0])
        hi = int(stataccum.GetMax()[0])
        a = slicer.util.array(ROIVolume.GetName())
        print a.max()
        labelValue=a.max()

        # Create the binary volume of the label
        thresholder = vtk.vtkImageThreshold()
        thresholder.SetInputConnection(ROIVolume.GetImageDataConnection())
        thresholder.SetInValue(1)
        thresholder.SetOutValue(0)
        thresholder.ReplaceOutOn()
        thresholder.ThresholdBetween(labelValue,labelValue)
        thresholder.SetOutputScalarType(inputVolume.GetImageData().GetScalarType())
        thresholder.Update()

        # use vtk's statistics class with the binary labelmap as a stencil
        stencil = vtk.vtkImageToImageStencil()
        stencil.SetInputConnection(thresholder.GetOutputPort())
        stencil.ThresholdBetween(1, 1)
        stat1 = vtk.vtkImageAccumulate()
        stat1.SetInputConnection(inputVolume.GetImageDataConnection())
        stencil.Update()
        stat1.SetStencilData(stencil.GetOutput())
        stat1.Update()

        return stat1.GetMean()[0]

    def run(self, firstVolume, ROIVolume):
        "Run the actual algorithm"
        if not firstVolume:
            logging.debug('Faltando primeiro volume.')
            slicer.util.errorDisplay('Faltando primeiro volume.')
            return False
        if ROIVolume and (firstVolume.GetID()==ROIVolume.GetID()):
            logging.debug('Primeiro volume e label sao iguais. Por favor corrija.')
            slicer.util.errorDisplay('Primeiro volume e label sao iguais. Por favor corrija.')
            return False

        logging.info('Processing started')

        # Buscando a media do primeiro Volume
        if ROIVolume:
            meanFirstVolume = self.mean(firstVolume, ROIVolume)
        else:
            a = slicer.util.array(firstVolume.GetName())
            meanFirstVolume = a.mean()

        print('Mean firstVolume: ', meanFirstVolume)

        # Identificar todos os volumes e processar
        for node in slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode'):
            logging.info('\nProcessando ' + node.GetName())
            if node.GetName() == firstVolume.GetName():
                logging.info('Ignorando primeiro volume: ' + node.GetName())
                continue

            if ROIVolume:
                if node.GetName() == ROIVolume.GetName():
                    logging.info('Ignorando label map: ' + node.GetName())
                    continue

            # Executar BrainsFit para corresgistro dos exames mais novos com o mais antigo
            fixedVolume = firstVolume
            movingVolume = node
            registeredVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", node.GetName() + ' Reg')
            logging.info('Registrando: ' + registeredVolume.GetName())
            brainsfitParameters = {'fixedVolume': fixedVolume.GetID(), 'movingVolume': movingVolume.GetID(), 'outputVolume': registeredVolume.GetID(), 'useRigid': True}
            self.cliNode = slicer.cli.run(slicer.modules.brainsfit, None, brainsfitParameters)

            while (self.cliNode.IsBusy()):
                slicer.app.processEvents()

            # Normalizando o segundo volume
            normVolume = registeredVolume
            if ROIVolume:
                meanRegisteredVolume = self.mean(normVolume, ROIVolume)
            else:
                a = slicer.util.array(normVolume.GetName())
                meanRegisteredVolume = a.mean()
            factor = meanRegisteredVolume / meanFirstVolume
            print('Mean First, Mean RegVolume, Factor: ', meanFirstVolume, meanRegisteredVolume, factor)
            print('Normalizando: ', normVolume.GetName())
            a = slicer.util.array(normVolume.GetName())
            a[:] = a / factor
            normVolume.GetImageData().Modified()

            #Subtracao manual para testes
            volumeLogic = slicer.modules.volumes.logic()
            subtractVolume = volumeLogic.CloneVolume(slicer.mrmlScene, normVolume, registeredVolume.GetName() + ' - ' + firstVolume.GetName())
            a = slicer.util.array(firstVolume.GetName())
            b = slicer.util.array(normVolume.GetName())
            c = slicer.util.array(subtractVolume.GetName())
            c[:]=0
            c[:]=numpy.absolute(a-b)
            # Aparando as "rebarbas da imagem"
            c[a==0]=0
            c[b==0]=0
            subtractVolume.GetImageData().Modified()

            # Exibir o resultado
            for color in ['Red', 'Yellow', 'Green']:
                slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(subtractVolume.GetID())

        #Executar VolumeRendering c/ MIP
        logic = slicer.modules.volumerendering.logic()
        volumeNode = subtractVolume
        displayNode = logic.CreateVolumeRenderingDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        displayNode.SetRaycastTechnique(2)
        logic.UpdateDisplayNodeFromVolumeNode(displayNode, volumeNode)
        displayNode.UnRegister(logic)
        volumeNode.AddAndObserveDisplayNodeID(displayNode.GetID())

        logging.info('Processing completed')

        return True

class TOFDiffTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    "Clear the scene"
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    "Run as few or as many tests as needed here."
    self.setUp()
    self.test_TOFDiff1()

  def test_TOFDiff1(self):
    " Test "

    self.delayDisplay("Starting the test")
    logging.info('test\n' % (name, url))
    self.delayDisplay('Test passed!')
