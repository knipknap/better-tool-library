from .camoticsserializer import CamoticsSerializer
from .fcserializer import FCSerializer
from .linuxcncserializer import LinuxCNCSerializer
from .fusionserializer import FusionToolsSerializer
from .fusionserializer import FusionJSONSerializer

serializers = {
    'camotics': CamoticsSerializer,
    'freecad': FCSerializer,
    'linuxcnc': LinuxCNCSerializer,
    'fusion_tools': FusionToolsSerializer,
    'fusion_json': FusionJSONSerializer,
}
