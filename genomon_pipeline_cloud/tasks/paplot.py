#! /usr/bin/env python

import pkg_resources
from ..abstract_task import *
 
class Paplot(Abstract_task):

    task_name = "paplot"

    def __init__(self, output_dir, task_dir, sample_conf, param_conf, mode):

        super(Paplot, self).__init__(
            pkg_resources.resource_filename("genomon_pipeline_cloud", "script/{}.sh".format(self.__class__.task_name)),
            "genomon/paplot",
            param_conf.get("paplot_" + mode, "resource"),
            output_dir + "/logging")
        
        self.task_file = self.task_file_generation(output_dir, task_dir, sample_conf, param_conf, mode)

    def task_file_generation(self, output_dir, task_dir, sample_conf, param_conf, mode):

        task_file = "{}/{}-tasks.tsv".format(task_dir, self.__class__.task_name)
        
        def to_oneliner(tag, stage, output_dir, output_suffix):
            
            header = []
            data = []
            counter = 0
            for sample in stage:
                counter += 1
                header.append("--input INPUT_" + tag.upper() + str(counter))
                if type(sample) == type(()):
                    sample = sample[0]
                data.append("%s/%s/%s%s" % (output_dir, sample, sample, output_suffix))
            
            return ["\t".join(header), "\t".join(data)]
        
        def to_oneliner_signature(tag, output_dir, sig_min, sig_max):
            
            header = []
            data = []
            counter = 0
            for sig in range(sig_min, sig_max+1):
                counter += 1
                header.append("--input INPUT_" + tag.upper() + str(counter))
                data.append("%s/pmsignature.%s.result.%d.json" % (output_dir, tag, sig))
            
            return ["\t".join(header), "\t".join(data)]
            
        items = {"star": ["", ""], "fusion": ["", ""], "qc": ["", ""], "sv": ["", ""], "mutation": ["", ""], "signature": ["", ""], "pmsignature": ["", ""]}

        if mode == "rna":
            items["star"]     = to_oneliner("starqc", sample_conf.qc, output_dir + "/star", ".Log.final.out")
            items["fusion"]   = to_oneliner("fusion", sample_conf.fusion, output_dir + "/fusion", ".genomonFusion.result.filt.txt")

        elif mode == "dna":
            items["qc"]       = to_oneliner("qc", sample_conf.qc, output_dir + "/qc", ".genomonQC.result.txt")
            items["sv"]       = to_oneliner("sv", sample_conf.sv_detection, output_dir + "/sv", ".genomonSV.result.filt.txt")
            # items["mutation"] = to_oneliner("mutation", sample_conf.mutation, output_dir + "/mutation", ".genomon_mutation.result.filt.txt")
            items["signature"]  = to_oneliner_signature("full", output_dir + "/pmsignature/sample", param_conf.getint("signature", "signum_min"), param_conf.getint("signature", "signum_max"))
            items["pmsignature"]= to_oneliner_signature("ind", output_dir + "/pmsignature/sample", param_conf.getint("pmsignature", "signum_min"), param_conf.getint("pmsignature", "signum_max"))
        
        header = []
        data = []
        for key in sorted(items.keys()):
            if len(items[key][0]) == 0:
                continue
            header.append(items[key][0])
            data.append(items[key][1])

        with open(task_file, 'w') as hout:

            print >> hout, '\t'.join(['\t'.join(header),
                                      "--input CONFIG_FILE",
                                      "--output-recursive OUTPUT_DIR",
                                      "--env REMARKS",
                                      "--env TITLE"])

            if param_conf.getboolean("paplot_" + mode, "enable"):
                remarks = param_conf.get("paplot_" + mode, "remarks")
                remarks += "<ul><li>genomon_pipeline_cloud-0.1.0a1</li>"
                for image in sorted(param_conf.get("paplot_" + mode, "software").split(",")):
                    remarks += "<li>genomon/" + image + ":latest</li>"
                remarks += "</ul>"
                
                print >> hout, '\t'.join(['\t'.join(data),
                                          param_conf.get("paplot_" + mode, "config_file"),
                                          output_dir + "/paplot/sample",
                                          remarks,
                                          param_conf.get("paplot_" + mode, "title")])

        return task_file

