import importlib
modules = ['app','data_preprocessing','anomaly_detection','output_reporting','utils.report_generation']
for m in modules:
    try:
        importlib.import_module(m)
        print(m + ' OK')
    except Exception as e:
        print(m + ' ERROR:', e)
