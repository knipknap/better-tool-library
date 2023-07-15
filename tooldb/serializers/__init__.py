from .dictserializer import DictSerializer
from .fcserializer import FCSerializer

serializers = {
    'dict': DictSerializer,
    'freecad': FCSerializer,
}
