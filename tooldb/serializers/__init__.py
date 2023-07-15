from .dictserializer import DictSerializer
from .fcserializer import FCSerializer
from .linuxcncserializer import LinuxCNCSerializer

serializers = {
    'dict': DictSerializer,
    'freecad': FCSerializer,
    'linuxcnc': LinuxCNCSerializer,
}
