from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMessageBox
from qgis.PyQt import QtGui
from qgis.core import *
import processing


class Linear(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('camadadeentrada', 'Camada de Entrada:', types=[QgsProcessing.TypeVectorLine], defaultValue=None))
        self.addParameter(QgsProcessingParameterExtent('extenso', 'Extensão:', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('resoluodagrade', 'Resolução da grade (m):', type=QgsProcessingParameterNumber.Double, defaultValue=1000))
        self.addParameter(QgsProcessingParameterFeatureSink('Grade_final', 'Resutado:', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(12, model_feedback)
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

        # Extrair por localização
        alg_params = {
            'INPUT': outputs['CriarGrade']['OUTPUT'],
            'INTERSECT': parameters['camadadeentrada'],
            'PREDICATE': 7,
            'OUTPUT': 'memory:'
        }
        outputs['ExtrairPorLocalizao'] = processing.run('native:extractbylocation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Soma de comprimentos de linha
        alg_params = {
            'COUNT_FIELD': 'COUNT',
            'LEN_FIELD': 'Dados_Oficiais',
            'LINES': parameters['camadadeentrada'],
            'POLYGONS': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['SomaDeComprimentosDeLinha'] = processing.run('qgis:sumlinelengths', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Build raw query
        alg_params = {
            'AREA': '',
            'EXTENT': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'QUERY': '<osm-script output=\"xml\" timeout=\"25\">\n    <union>\n        <query type=\"way\">\n            <has-kv k=\"highway\"/>\n            <bbox-query {{bbox}}/>\n        </query>\n    </union>\n    <union>\n        <item/>\n        <recurse type=\"down\"/>\n    </union>\n    <print mode=\"body\"/>\n</osm-script>',
            'SERVER': 'http://www.overpass-api.de/api/interpreter'
        }
        outputs['BuildRawQuery'] = processing.run('quickosm:buildrawquery', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Baixar arquivo
        alg_params = {
            'URL': outputs['BuildRawQuery']['OUTPUT_URL'],
            'OUTPUT': 'memory:'
        }
        outputs['BaixarArquivo'] = processing.run('native:filedownloader', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(5)
        if feedback.isCanceled():
            return {}

        # Concatenação de cadeias de caracteres
        alg_params = {
            'INPUT_1': outputs['BaixarArquivo']['OUTPUT'],
            'INPUT_2': QgsExpression('\'|layername=lines\'').evaluate()
        }
        outputs['ConcatenaoDeCadeiasDeCaracteres'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(6)
        if feedback.isCanceled():
            return {}

        # Reprojetar camada
        alg_params = {
            'INPUT': outputs['ConcatenaoDeCadeiasDeCaracteres']['CONCATENATION'],
            'TARGET_CRS': 'ProjectCrs',
            'OUTPUT': 'memory:'
        }
        outputs['ReprojetarCamada'] = processing.run('native:reprojectlayer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(7)
        if feedback.isCanceled():
            return {}

        # Recortar
        alg_params = {
            'INPUT': outputs['ReprojetarCamada']['OUTPUT'],
            'OVERLAY': outputs['ExtrairPorLocalizao']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['Recortar'] = processing.run('native:clip', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(8)
        if feedback.isCanceled():
            return {}

        # Extrair por expressão
        alg_params = {
            'EXPRESSION': '\"highway\"=\'primary\' OR \"highway\"=\'primary_link\' OR \"highway\"=\'secondary\' OR \"highway\"=\'secondary_link\' OR \"highway\"=\'tertiary_link\' OR \"highway\"=\'tertiary\' OR \"highway\"=\'residential\' OR \"highway\"=\'trunk\' OR \"highway\"=\'trunk_link\' OR \"highway\"=\'motorway\' OR \"highway\"=\'motorway_link\' OR \"highway\"=\'living_street\'',
            'INPUT': outputs['Recortar']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['ExtrairPorExpresso'] = processing.run('native:extractbyexpression', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(9)
        if feedback.isCanceled():
            return {}

        # Soma de comprimentos de linha
        alg_params = {
            'COUNT_FIELD': 'Cont_OSM',
            'LEN_FIELD': 'Dados_OSM',
            'LINES': outputs['ExtrairPorExpresso']['OUTPUT'],
            'POLYGONS': outputs['SomaDeComprimentosDeLinha']['OUTPUT'],
            'OUTPUT': 'memory:'
        }
        outputs['SomaDeComprimentosDeLinha'] = processing.run('qgis:sumlinelengths', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(10)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Resultado',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': 'if(  \"Dados_OSM\"  = 0 AND  \"Dados_Oficiais\"  = 0, NULL, \"Dados_Oficiais\" - \"Dados_OSM\")',
            'INPUT': outputs['SomaDeComprimentosDeLinha']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': 'memory:'
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(11)
        if feedback.isCanceled():
            return {}

        # Calculadora de campo
        alg_params = {
            'FIELD_LENGTH': 10,
            'FIELD_NAME': 'Resultado_Normalizado',
            'FIELD_PRECISION': 3,
            'FIELD_TYPE': 0,
            'FORMULA': 'CASE \nWHEN  \"Resultado\" < 0 THEN  -\"Resultado\"  / minimum(\"Resultado\")\nWHEN  \"Resultado\" > 0 THEN  \"Resultado\"  / maximum(\"Resultado\")\nEND',
            'INPUT': outputs['CalculadoraDeCampo']['OUTPUT'],
            'NEW_FIELD': True,
            'OUTPUT': parameters['Grade_final']
        }
        outputs['CalculadoraDeCampo'] = processing.run('qgis:fieldcalculator', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Grade_final'] = outputs['CalculadoraDeCampo']['OUTPUT']
        
        return results

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Completude Linear'

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
        return 'Geometria'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Linear()
