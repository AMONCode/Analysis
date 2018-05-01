# Streams for AMON

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
          }

inv_streams = dict(map(reversed,streams.items()))

alert_streams = {
            "IC-HAWC":1,
            "IC-Swift":2,
            "IC-HESE-EHE":3,
            "IC-Fermi":4,
            "OFU-Alerts":5,
            "GFU-Alerts":6,
            "HWC-GRBlike-Alerts":7,
}

inv_alert_streams = dict(map(reversed,alert_streams.items()))
