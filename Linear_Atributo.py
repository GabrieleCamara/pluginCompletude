from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.PyQt import QtGui
from qgis.core import *
import processing


class Linear_Atributo(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterExtent('extenso', 'Extensão:', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('resoluodagrade', 'Resolução da grade (m):', type=QgsProcessingParameterNumber.Double, defaultValue=1000))
        self.addParameter(QgsProcessingParameterFeatureSink('Unido_final', 'Resultado:', optional=True, type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(13, model_feedback)
        results = {}
        outputs = {}

        # Criar grade
        alg_params = {
            'CRS': 'ProjectCrs',
            'EXTENT': parameters['extenso'],
            'HOVERLAY': 0,
            'HSPACING': parameters['resoluodagrade'],
            'TYPE': 2,
            'VOVERLAY': 0,
            'VSPACING': parameters['resoluodagrade'],
            'OUTPUT': 'memory:'
        }
        outputs['CriarGrade'] = processing.run('qgis:creategrid', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Build raw query
        alg_params = {
            'AREA': '',
            'EXTENT': outputs['CriarGrade']['OUTPUT'],
            'QUERY': '<osm-script output=\"xml\" timeout=\"25\">\n    <union>\n        <query type=\"way\">\n            <has-kv k=\"highway\"/>\n            <bbox-query {{bbox}}/>\n        </query>\n    </union>\n    <union>\n        <item/>\n        <recurse type=\"down\"/>\n    </union>\n    <print mode=\"body\"/>\n</osm-script>',
            'SERVER': 'http://www.overpass-api.de/api/interpreter'
        }
        outputs['BuildRawQuery'] = processing.run('quickosm:buildrawquery', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Baixar arquivo
        alg_params = {
            'URL': outputs['BuildRawQuery']['OUTPUT_URL'],
            'OUTPUT': 'memory:'
        }
        outputs['BaixarArquivo'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Polígonos para linhas
        alg_params = {
            'INPUT': outputs['CriarGrade']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['PolgonosParaLinhas'] = processing.run('qgis:polygonstolines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Concatenação de cadeias de caracteres
        alg_params = {
            'INPUT_1': outputs['BaixarArquivo']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=lines\'').evaluate()
        }
        outputs['ConcatenaoDeCadeiasDeCaracteres'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada
        alg_params = {
            'INPUT': outputs['ConcatenaoDeCadeiasDeCaracteres']['CONCATENATION'],
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': 'memory:'
        }
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
            'OVERLAY': outputs['CriarGrade']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Linhas com quebra
        alg_params = {
            'INPUT': outputs['Recortar']['OUTPUT'],
            'LINES': outputs['PolgonosParaLinhas']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['LinhasComQuebra'] = processing.run('native:splitwithlines', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Unir atributos pela posição
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'INPUT': outputs['LinhasComQuebra']['OUTPUT'],
            'JOIN': outputs['CriarGrade']['OUTPUT'],
            'JOIN_FIELDS': None,
            'METHOD': 1,
            'PREDICATE': 5,
            'PREFIX': '',
            'OUTPUT': 'memory:'
        }
        outputs['UnirAtributosPelaPosio'] = processing.run('qgis:joinattributesbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Categoriza',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 1,
            'FORMULA': 'IF(\"name\" IS NULL, 0, 1)',
            'INPUT': outputs['UnirAtributosPelaPosio']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': 'memory:'
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Porc_Preenchida',
            'FIELD_PRECISION': 1,
            'FIELD_TYPE': 0,
            'FORMULA': 'count(\"Categoriza\", \"id\", \"Categoriza\" = 1) / count(\"Categoriza\", \"id\")*100',
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': 'memory:'
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Dissolver
        alg_params = {
            'FIELD': 'id',
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['Dissolver'] = processing.run('native:dissolve', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(12)
        if feedback.isCanceled():
            return {}

        # Unir atributos pelo valor do campo
        alg_params = {
            'DISCARD_NONMATCHING': False,
            'FIELD': 'id',
            'FIELDS_TO_COPY': None,
            'FIELD_2': 'id',
            'INPUT': outputs['CriarGrade']['OUTPUT'],
            'INPUT_2': outputs['Dissolver']['OUTPUT'],
            'METHOD': 1,
            'PREFIX': '',
            'OUTPUT': parameters['Unido_final']
        }
        outputs['UnirAtributosPeloValorDoCampo'] = processing.run('native:joinattributestable', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
                
        results['Unido_final'] = outputs['UnirAtributosPeloValorDoCampo']['OUTPUT']
        
        return results
        
    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Completude Semântica Linear (name)'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Atributo'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Linear_Atributo()
