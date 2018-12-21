import os
import unittest
import vtk, qt, ctk, slicer, numpy
from slicer.ScriptedLoadableModule import *
import logging

# TOFVol

class TOFVol(ScriptedLoadableModule):
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "TOF Vol" # TODO make this more human readable by adding spaces
        self.parent.categories = ["HCFMRP"]
        self.parent.dependencies = []
        self.parent.contributors = ["Julio C. Ferranti (FMRP-USP)"]
        self.parent.helpText = "Calculo do volume TOF pre e pes operatorio"
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = ""

# TOFVolWidget
class TOFVolWidget(ScriptedLoadableModuleWidget):
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

        # input fiducial selector
        self.fiducialSelector = slicer.qMRMLNodeComboBox()
        self.fiducialSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
        self.fiducialSelector.selectNodeUponCreation = True
        self.fiducialSelector.addEnabled = False
        self.fiducialSelector.removeEnabled = False
        self.fiducialSelector.noneEnabled = False
        self.fiducialSelector.showHidden = False
        self.fiducialSelector.showChildNodeTypes = False
        self.fiducialSelector.setMRMLScene( slicer.mrmlScene )
        self.fiducialSelector.setToolTip( "Ponto fiducial base para criacao da ROI" )
        parametersFormLayout.addRow("Ponto Fiducial: ", self.fiducialSelector)

        # Buttons
        self.setROIButton = qt.QPushButton("Criar ROI")
        self.setROIButton.toolTip = ""
        self.setROIButton.enabled = False
        parametersFormLayout.addRow(self.setROIButton)

        self.applyButton = qt.QPushButton("Iniciar")
        self.applyButton.toolTip = "Executar."
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
        self.setROIButton.connect('clicked(bool)', self.createROI)
        self.fiducialSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
        self.baseSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.setBackground)

        # Refresh Apply button state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.baseSelector.currentNode()
        self.setROIButton.enabled = self.baseSelector.currentNode() and self.fiducialSelector.currentNode()

        #verificando se tem uma ROI
        for node in slicer.util.getNodesByClass('vtkMRMLAnnotationROINode'):
            self.setROIButton.enabled = False

    def setBackground(self):
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(self.baseSelector.currentNode().GetID())

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


    def createROI(self):
        # Verificar se ha apenas um fiducial
        fiducialNode = self.fiducialSelector.currentNode()
        numFiducials = fiducialNode.GetNumberOfFiducials()
        if numFiducials > 1:
            slicer.util.messageBox("Nao ha' fiducial definido para criar a ROI.")
            return
        if numFiducials > 1:
            slicer.util.messageBox("Encontrado mais de 1 fiducial.\nSo' pode haver um.")
            return

        # Localizando o Fiducial e criando a ROI
        L = 50.0
        P = 35.0
        A = 12.5

        ras = [0.0, 0.0, 0.0]
        pos = [0.0, 0.0, 0.0]
        fiducialNode.GetNthFiducialPosition(0, ras)

        pos[0] = ras[0] - 10
        pos[1] = ras[1] - 25
        pos[2] = ras[2] + 7.5

        min=0; max=0; minvalue=0

        ROI = slicer.vtkMRMLAnnotationROINode()
        ROI.SetName('RoiNode')
        slicer.mrmlScene.AddNode(ROI)
        ROI.SetXYZ(pos)
        ROI.SetRadiusXYZ(L, P, A)
        ROI.SetDisplayVisibility(True)

        self.setROIButton.enabled = False

        slicer.app.processEvents() #atualiza tela

        return ROI

    def onApplyButton(self):
        self.applyButton.setText("Aguarde...")
        self.applyButton.setEnabled(False)
        self.progressBar.setVisible(True)
        inputVolume = self.baseSelector.currentNode()
        cropLogic = slicer.modules.cropvolume.logic()
        volumesLogic = slicer.modules.volumes.logic()
        label=1
        perc=0.75
        hasROI = False

        logging.info('Processing started')

        # Criar tabela para os dados
        logging.info('Criando a tabela')
        table = slicer.vtkMRMLTableNode()
        tableWasModified = table.StartModify()
        table.SetName("Export Table")
        table.SetUseColumnNameAsColumnHeader(True)
        col = table.AddColumn(); col.SetName("Volume")
        col = table.AddColumn(); col.SetName("Qtde")
        col = table.AddColumn(); col.SetName("Min-Max")
        col = table.AddColumn(); col.SetName("Range")

        # Hierarquia para modelos 3D
        modelHNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLModelHierarchyNode')
        modelHNode.SetName('Models')
        modelHNode = slicer.mrmlScene.AddNode(modelHNode)

        # Atualiza tela
        slicer.app.processEvents()

        # Criando a ROI
        logging.info('Criar ROI a partir do Fiducial')
        for node in slicer.util.getNodesByClass('vtkMRMLAnnotationROINode'):
            ROI = node
            hasROI = True

        if not hasROI:
            ROI = self.createROI()

        # Calculando media do volume inicial
        logging.info('Calcular media volume inicial: ' + inputVolume.GetName())
        arrayInputVolume = slicer.util.array(inputVolume.GetName())
        meanInputVolume = arrayInputVolume.mean()

        # Realizar o crop no primeiro volume
        logging.info('Crop do volume inicial')
        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", inputVolume.GetName() + ' cropped')
        cropLogic.CropInterpolated(ROI, inputVolume, outputVolume, False, 1.0, 2, 0)

        # Calculo dos pontos mais intensos do primeiro volume
        logging.info("Calculando pontos mais intensos do volume inicial")
        arrayNode = slicer.util.array(outputVolume.GetName())
        min = arrayNode.min()
        max = arrayNode.max()
        minValue = max - ((max-min)*perc)
        arrayValue = arrayNode[arrayNode>=minValue]
        meanValue = arrayValue.mean()
        countValue = len(arrayValue)

        # Atualiza tela
        slicer.app.processEvents()

        #segmentando o primeiro volume
        logging.info('Segmentando volume inicial')
        labelMap = volumesLogic.CreateAndAddLabelVolume(slicer.mrmlScene, outputVolume, outputVolume.GetName() + '-label' )
        labelArray = slicer.util.array(labelMap.GetName())
        labelArray[arrayNode>minValue] = label
        labelMap.GetImageData().Modified()
        inputLabelMap = labelMap

        # Apagando o volume cropped
        slicer.mrmlScene.RemoveNode(outputVolume)

        # Criar modelo 3D
        logging.info('Criar modelo 3D do volume inicial')
        parameters = {}
        parameters["InputVolume"] = labelMap.GetID()
        parameters["Name"] = labelMap.GetName() + '-model'
        parameters['ModelSceneFile'] = modelHNode.GetID()
        modelMaker = slicer.modules.modelmaker
        slicer.cli.run(modelMaker, None, parameters, True)

        # Atualiza tela
        slicer.app.processEvents()

        # Popular tabela com os dados do primeiro volume
        logging.info('Popular tabela')
        rowIndex = table.AddEmptyRow()
        table.SetCellText(rowIndex, 0, inputVolume.GetName())
        table.SetCellText(rowIndex, 1, str(countValue))
        table.SetCellText(rowIndex, 2, str(int(min)) + " - " + str(int(max)))
        table.SetCellText(rowIndex, 3, str(int(minValue)) + " - " + str(int(max)))

        # Atualiza tela
        slicer.app.processEvents()

        # Identificar todos os volumes e processar
        for node in slicer.util.getNodesByClass('vtkMRMLScalarVolumeNode'):
            logging.info('\nProcessando ' + node.GetName())
            if node.GetName() == inputVolume.GetName():
                logging.info('Ignorando volume: ' + node.GetName())
                continue
            if node.GetClassName() == "vtkMRMLLabelMapVolumeNode":
                logging.info('Ignorando label: ' + node.GetName())
                continue

            # Executar BrainsFit para corresgistro dos exames mais novos com o mais antigo
            logging.info('Registrando o volume')
            fixedVolume = inputVolume
            movingVolume = node
            registeredVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", node.GetName() + ' Reg')
            brainsfitParameters = {'fixedVolume': fixedVolume.GetID(), 'movingVolume': movingVolume.GetID(), 'outputVolume': registeredVolume.GetID(), 'useRigid': True}
            self.cliNode = slicer.cli.run(slicer.modules.brainsfit, None, brainsfitParameters)

            while (self.cliNode.IsBusy()):
                slicer.app.processEvents()

            # Normalizar volumes
            logging.info('Normalizando o volume')
            arrayRegisteredVolume = slicer.util.array(registeredVolume.GetName())
            meanRegisteredVolume = arrayRegisteredVolume.mean()
            factor = meanRegisteredVolume / meanInputVolume
            arrayRegisteredVolume[:] = arrayRegisteredVolume / factor
            arrayRegisteredVolume[:] = numpy.around(arrayRegisteredVolume, 0)

            # Crop Interpolated
            logging.info('Crop do volume')
            outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode", registeredVolume.GetName() + ' cropped')
            cropLogic.CropInterpolated(ROI, registeredVolume, outputVolume, False, 1.0, 2, 0)

            # Calculo dos pontos mais intensos do volume corregistrado
            print("Calculando")
            arrayNode = slicer.util.array(outputVolume.GetName())
            arrayNode[:] = numpy.around(arrayNode, 0)
            min = arrayNode.min()
            max = arrayNode.max()
            minValue = max - ((max-min)*perc)
            arrayValue = arrayNode[arrayNode>=minValue]
            meanValue = arrayValue.mean()
            countValue = len(arrayValue)

            # Atualiza tela
            slicer.app.processEvents()

            #segmentando o volume
            logging.info('Segmentando Volume')
            label = label + 1
            labelMap = volumesLogic.CreateAndAddLabelVolume(slicer.mrmlScene, outputVolume, outputVolume.GetName() + '-label' )
            labelArray = slicer.util.array(labelMap.GetName())
            labelArray[arrayNode>minValue] = label
            labelMap.GetImageData().Modified()

            # Apagando o volume cropped
            slicer.mrmlScene.RemoveNode(outputVolume)

            # Criar modelo 3D
            logging.info('Criar Modelo 3D')
            parameters = {}
            parameters["InputVolume"] = labelMap.GetID()
            parameters["Name"] = labelMap.GetName() + '-model'
            parameters['ModelSceneFile'] = modelHNode.GetID()
            modelMaker = slicer.modules.modelmaker
            slicer.cli.run(modelMaker, None, parameters, True)

            # Atualiza tela
            slicer.app.processEvents()

            # Popular tabela com os dados
            logging.info('Popular tabela')
            rowIndex = table.AddEmptyRow()
            table.SetCellText(rowIndex, 0, node.GetName())
            table.SetCellText(rowIndex, 1, str(countValue))
            table.SetCellText(rowIndex, 2, str(int(min)) + " - " + str(int(max)))
            table.SetCellText(rowIndex, 3, str(int(minValue)) + " - " + str(int(max)))
            rowIndex += 1

        # Exibir o resultado
        logging.info('Exibir resultado')
        for color in ['Red', 'Yellow', 'Green']:
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(inputVolume.GetID())
            slicer.app.layoutManager().sliceWidget(color).sliceLogic().GetSliceCompositeNode().SetLabelVolumeID(inputLabelMap.GetID())

        # Add table to the scene and show it
        logging.info('Adicionar tabela e exibir')
        slicer.mrmlScene.AddNode(table)
        slicer.app.layoutManager().setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutFourUpTableView)
        slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveTableID(table.GetID())
        slicer.app.applicationLogic().PropagateTableSelection()
        table.EndModify(tableWasModified)

        # Atualiza tela
        slicer.app.processEvents()

        logging.info('Processing completed')

        self.applyButton.setText("Iniciar")
        self.applyButton.setEnabled(True)
        self.progressBar.setVisible(False)

        return
