import os
import glob
from zipfile import ZipFile
import json
from .. import Library, Tool
from ..params import Param, DistanceParam, IntParam, BoolParam
from ..toolmaterial import HSS, Carbide
from .. import Shape
from .serializer import Serializer
from FreeCAD import Console

# fusion tools may defined in imperial or metric units.
# map those unit strings to something FreeCAD.Units understands
UNIT_MAP = {
    "millimeters": "mm",
    "inches": "in",
}

# map the type of the tool in a .tools database to a shape file.
# some user visible tool types in fusion have identical internal representation
#  I.E.: chamfer mills & spot_drills
# Custom form tools, thread mills, and taps are not supported yet
# (thread mills can be single or multi-pitch, we would need to generate the
# shape files at runtime in order to suppport them properly)
SHAPE_FILES = {
    # milling
    "ball end mill": "ball_end_mill",
    "bull nose end mill": "bull_nose_end_mill",
    "chamfer mill": "chamfer_mill",
    "dovetail mill": "dovetail_mill",
    "face mill": "face_mill",
    "flat end mill": "flat_end_mill",
    "form mill": None,
    "lollipop mill": "lollipop_mill",
    "radius mill": "radius_mill",
    "slot mill": "slot_mill",
    "tapered mill": "tapered_mill",
    "thread mill": None,
    # hole-making
    "boring bar": "flat_end_mill",
    "counter bore": "flat_end_mill",
    "center drill": "center_drill",
    "spot drill": "chamfer_mill",
    "counter sink": "counter_sink",
    "drill": "drill",
    "reamer": "reamer",
    "tap left hand": "tap",
    "tap right hand": "tap",
}


# name of the json file in a .tools zipped database
TOOLS_FILENAME = "tools.json"


class FusionSerializer(Serializer):
    """Fusion 360 allows for distribution of tool libraries in either plain
    json format, or as a zip archive of the same json data. Define this base
    class to to the work, then subclass it with some shims for reading in the
    json data"""

    def __init__(self, path, *args, **kwargs):
        self.set_tool_dir(path)

    def set_tool_dir(self, path):
        self.path = path
        if os.path.exists(self.path) and not os.path.isdir(self.path):
            raise ValueError(repr(self.path) + " is not a directory")

    def _library_filename_from_id(self, id):
        return os.path.join(self.path, id + self.LIBRARY_EXT)

    def _get_library_ids(self):
        files = glob.glob(os.path.join(self.path, "*" + self.LIBRARY_EXT))
        return sorted(
            self._library_id_from_filename(f) for f in files if os.path.isfile(f)
        )

    def deserialize_libraries(self):
        return [self.deserialize_library(id) for id in self._get_library_ids()]

    @classmethod
    def can_deserialize_library(cls):
        return True

    def deserialize_library(self, id):
        lib_filename = self._library_filename_from_id(id)
        return self.deserialize_library_from_file(lib_filename)

    def _get_library_data(self, filename):
        raise NotImplementedError

    def deserialize_library_from_file(self, filename):
        data = self._get_library_data(filename)
        library = Library(id, id=id)
        # tools are indexed by number in a dict inside the "data" key
        for toolitem in data["data"]:
            # each entry has its own unit system specification
            lunit = UNIT_MAP[toolitem["unit"]]
            shapefile = SHAPE_FILES.get(toolitem["type"], None)
            if shapefile is None:
                Console.PrintWarning(
                    f"skipping tool: {toolitem['description']} "
                    f"with unimplemented type '{toolitem['type']}'\n"
                )
                continue
            tname = "_fusion_" + shapefile
            tpath = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "resources/shapes",
                tname + ".fcstd",
            )
            toolshape = Shape(tname, tpath)
            tool = Tool(toolitem["description"], toolshape, filename=filename)
            # set a descriptive label if one is not present in the json data
            geom = toolitem["geometry"]
            if not (tlabel := toolitem["description"]):
                tool.set_label(toolitem["type"] + " - dia " + str(geom["DC"]))
            else:
                tool.set_label(tlabel)
            # some parameters are the same for all tool shapes
            tool.shape.set_param(
                "Diameter", DistanceParam(name="Diameter", unit=lunit, v=geom["DC"])
            )
            tool.shape.set_param(
                "Length", DistanceParam(name="Length", unit=lunit, v=geom["OAL"])
            )
            tool.shape.set_param(
                "NeckLength",
                DistanceParam(name="NeckLength", unit=lunit, v=geom["shoulder-length"]),
            )
            tool.shape.set_param(
                "CuttingEdgeHeight",
                DistanceParam(name="CuttingEdgeHeight", unit=lunit, v=geom["LCF"]),
            )
            tool.shape.set_param(
                "ShankDiameter",
                DistanceParam(name="ShankDiameter", unit=lunit, v=geom["SFDM"]),
            )
            # fill in the remaining properties based on the tool type
            match toolitem["type"]:
                case "ball end mill" | "flat end mill" | "reamer" | "boring bar" | "counter bore" | "lollipop mill":
                    pass
                case "bull nose end mill":
                    tool.shape.set_param(
                        "TorusRadius",
                        DistanceParam(name="TorusRadius", unit=lunit, v=geom["RE"]),
                    )
                case "chamfer mill":
                    tool.shape.set_param(
                        "TipDiameter",
                        DistanceParam(
                            name="TipDiameter", unit=lunit, v=geom["tip-diameter"]
                        ),
                    )
                    tool.shape.set_param(
                        "TipAngle", Param(name="TipAngle", unit="deg", v=geom["TA"] * 2)
                    )
                case "spot drill":
                    tool.shape.set_param(
                        "TipDiameter",
                        DistanceParam(
                            name="TipDiameter", unit=lunit, v=geom["tip-diameter"]
                        ),
                    )
                    tool.shape.set_param(
                        "TipAngle", Param(name="TipAngle", unit="deg", v=geom["SIG"])
                    )
                case "drill":
                    tool.shape.set_param(
                        "TipAngle", Param(name="TipAngle", unit="deg", v=geom["SIG"])
                    )
                case "dovetail mill":
                    tool.shape.set_param(
                        "TorusRadius",
                        DistanceParam(name="TorusRadius", unit=lunit, v=geom["RE"]),
                    )
                    tool.shape.set_param(
                        "CuttingAngle",
                        Param(name="CuttingAngle", unit="deg", v=geom["TA"]),
                    )
                case "face mill":
                    tool.shape.set_param(
                        "TorusRadius",
                        DistanceParam(name="TorusRadius", unit=lunit, v=geom["RE"]),
                    )
                    tool.shape.set_param(
                        "TaperAngle", Param(name="TaperAngle", unit="deg", v=geom["TA"])
                    )
                case "radius mill":
                    tool.shape.set_param(
                        "TipLength",
                        DistanceParam(
                            name="TipLength", unit=lunit, v=geom["tip-length"]
                        ),
                    )
                    tool.shape.set_param(
                        "CornerRadius",
                        DistanceParam(name="CornerRadius", unit=lunit, v=geom["RE"]),
                    )
                case "slot mill":
                    tool.shape.set_param(
                        "CornerRadius",
                        DistanceParam(name="CornerRadius", unit=lunit, v=geom["RE"]),
                    )
                case "tapered mill":
                    tool.shape.set_param(
                        "TorusRadius",
                        DistanceParam(name="TorusRadius", unit=lunit, v=geom["RE"]),
                    )
                    tool.shape.set_param(
                        "TaperAngle", Param(name="TaperAngle", unit="deg", v=geom["TA"])
                    )
                case "center drill":
                    tool.shape.set_param(
                        "TaperAngle", Param(name="TaperAngle", unit="deg", v=geom["TA"])
                    )
                    tool.shape.set_param(
                        "TipAngle", Param(name="TipAngle", unit="deg", v=geom["SIG"])
                    )
                    tool.shape.set_param(
                        "TipLength",
                        DistanceParam(
                            name="TipLength", unit=lunit, v=geom["tip-length"]
                        ),
                    )
                    tool.shape.set_param(
                        "TipDiameter",
                        DistanceParam(
                            name="TipDiameter", unit=lunit, v=geom["tip-diameter"]
                        ),
                    )
                case "tap right hand":
                    tool.shape.set_param(
                        "RightHanded",
                        BoolParam(name="RightHanded", v=True),
                    )
                    tool.shape.set_param(
                        "ThreadPitch",
                        DistanceParam(name="ThreadPitch", unit=lunit, v=geom["TP"]),
                    )
                case "tap left hand":
                    tool.shape.set_param(
                        "RightHanded",
                        BoolParam(name="RightHanded", v=False),
                    )
                    tool.shape.set_param(
                        "ThreadPitch",
                        DistanceParam(name="ThreadPitch", unit=lunit, v=geom["TP"]),
                    )
                case "counter sink":
                    tool.shape.set_param(
                        "TipDiameter",
                        DistanceParam(
                            name="TipDiameter", unit=lunit, v=geom["tip-diameter"]
                        ),
                    )
                    tool.shape.set_param(
                        "TipAngle",
                        Param(name="TipAngle", unit="deg", v=geom["SIG"] * 2),
                    )
                case _ as unknown_tool_type:
                    raise ValueError(f"Unknown tool type: {unknown_tool_type}")
            # Finally, set material and cutting parameters
            if tool_mat := toolitem["BMC"] == "hss":
                tool.shape.set_material(HSS)
            elif tool_mat == "carbide":
                tool.shape.set_material(Carbide)
            else:
                # default to hss. fusion allows for ceramics or unspecified
                # tool materials, while we currently only allow for carbide and HSS
                tool.shape.set_material(HSS)
            tool.shape.set_param("Flutes", IntParam(name="Flutes", v=geom["NOF"]))
            # fusion encodes a complex set of start values for different
            # operations and workpiece materials, but FreeCAD stores this
            # data in the ToolController objects, not directly in tools.
            # Just set a dummy value for the chipload.
            tool.shape.set_param(
                "Chipload", DistanceParam(name="Chipload", unit="mm", v=0.01)
            )
            # notes and vendor info may be blank, but the dictionary keys are always present
            tool.set_supplier(toolitem["vendor"])
            tool.set_notes(toolitem["post-process"]["comment"])
            tool_number = toolitem["post-process"]["number"]
            library.add_tool(tool, tool_number)
            Console.PrintMessage(f"Added tool number {tool_number} to the library\n")
        return library


class FusionToolsSerializer(FusionSerializer):
    NAME = "Fusion 360"
    LIBRARY_EXT = ".tools"

    def _get_library_data(self, filename):
        with ZipFile(filename, "r") as z:
            data = json.loads(z.read(TOOLS_FILENAME))
        return data


class FusionJSONSerializer(FusionSerializer):
    NAME = "Fusion 360"
    LIBRARY_EXT = ".json"

    def _get_library_data(self, filename):
        with open(filename, "rb") as f:
            data = json.load(f)
        return data
