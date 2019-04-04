import bpy
import sys
import json


index = sys.argv.index("--")
config_file_location = sys.argv[index + 1]
output_file = sys.argv[index + 2]


# At first we delete the default cube in the document when present

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

configFile = open(config_file_location)

try:
    config = json.load(configFile, encoding='utf-8')
finally:
    configFile.close()

modifiedObject = None

for configEntry in config:
    left = configEntry['left']
    right = configEntry['right']
    mode = configEntry['mode']

    if left['type'] == 'file':
        bpy.ops.import_mesh.stl(filepath=left['file'])
        obj_left = bpy.context.selected_objects[0]
    else:
        obj_left = modifiedObject
    
    if right['type'] == 'file':
        bpy.ops.import_mesh.stl(filepath=right['file'])
        obj_right = bpy.context.selected_objects[0]
    else:
        obj_right = modifiedObject

    bpy.context.scene.objects.active = obj_left
    bpy.ops.object.modifier_add(type='BOOLEAN')

    bpy.context.object.modifiers[0].object = obj_right
    bpy.context.object.modifiers[0].operation = configEntry['mode']
    bpy.ops.object.modifier_apply(modifier='Boolean')


    bpy.context.scene.objects.active = obj_right
    bpy.ops.object.delete()

    modifiedObject = obj_left


bpy.context.scene.objects.active = modifiedObject
bpy.ops.export_mesh.stl(filepath=output_file)
