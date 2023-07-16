from .camoticsserializer import CamoticsSerializer
from .dictserializer import DictSerializer
from .fcserializer import FCSerializer
from .linuxcncserializer import LinuxCNCSerializer

serializers = {
    'camotics': CamoticsSerializer,
    'dict': DictSerializer,
    'freecad': FCSerializer,
    'linuxcnc': LinuxCNCSerializer,
}
