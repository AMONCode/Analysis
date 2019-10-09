# ID numbers for the different datasets
# Notice that some observatories have different streams

from builtins import map
streams = {
            "IC-Singlet" : 0,
            "IC-HESE" : 10,
            "IC-EHE": 11,
            "IC-OFU_MASTER": 12,
            "IC-OFU_ASAS-SN": 13,
            "IC-OFU_LCGOT":14,
            "IC-OFU_PTF": 15,
            "IC-SF_Fermi":16,
            "IC-SF_HAWC":17,
            "IC-SF_HESS":18,
            "IC-SF_MAGIC":19,
            "IC-SF_Veritas":20,
            "IC-GFU":21,
            "SWIFT":4,
            "FACT":5,
            "HAWC-DM":7,
            "HAWC-Burst":8,
            "Antares":1,
            "Auger":3,
            "Fermi":23,
            "IC-Gold":24,
            "IC-Bronze":25,
          }

inv_streams = dict(list(map(reversed,list(streams.items()))))

# Number for the alert streams for the different
# correlation analyses/pass-through analyses.

alert_streams = {
            "IC-HAWC":1,
            "IC-Swift":2,
            "IC-HESE-EHE":3,
            "IC-Fermi":4,
            "OFU-Alerts":5,
            "GFU-Alerts":6,
            "HWC-GRBlike-Alerts":7,
            "Antares-Fermi":8,
            "IC-Gold-Bronze":9,
}

inv_alert_streams = dict(list(map(reversed,list(alert_streams.items()))))

# ID number for the streams that are sent to GCN
gcn_streams = {
            "IC-OFU":0,
            "IC-HESE":1,
            "IC-EHE":2,
            "IC-HAWC":9,
            "IC-Fermi":4,
            "OFU-Alerts1":12,
            "OFU-Alerts2":13,
            "OFU-Alerts3":14,
            "OFU-Alerts4":15,
            "GFU-Alerts1":16,
            "GFU-Alerts2":17,
            "GFU-Alerts3":18,
            "GFU-Alerts4":19,
            "HWC-GRBlike-Alerts":7,#171 in GCN socket information
            "Antares-Fermi":8,#170 in GCN socket information
            "IC-Gold":24,#173 in GCN socket info
            "IC-Bronze":25,#174 in GCN socket info
            "Gamma-Nu-Coinc":172,
}

inv_gcn_streams = dict(list(map(reversed,list(gcn_streams.items()))))
