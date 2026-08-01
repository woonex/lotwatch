FEATURES = [
    {"key": "drivetrain", "label": "Drivetrain", "type": "select", "group": "Drivetrain",
     "options": [["gas", "Gas"], ["hybrid", "Hybrid"], ["phev", "PHEV"], ["ev", "EV"]]},
    {"key": "drive_type", "label": "Drive Type", "type": "select", "group": "Drivetrain",
     "options": [["fwd", "FWD"], ["rwd", "RWD"], ["awd", "AWD"], ["4x4", "4x4"]]},
    {"key": "parking_sensors", "label": "Parking Sensors", "type": "boolean", "group": "Safety"},
    {"key": "camera_360", "label": "360° Camera", "type": "boolean", "group": "Safety"},
    {"key": "seat_material", "label": "Seat Material", "type": "select", "group": "Seats",
     "options": [["cloth", "Cloth"], ["cloth_leather", "Cloth/Leather"], ["leather", "Leather"]]},
    {"key": "heated_seats", "label": "Heated Seats", "type": "boolean", "group": "Seats"},
    {"key": "ventilated_seats", "label": "Ventilated Seats", "type": "boolean", "group": "Seats"},
    {"key": "heated_steering", "label": "Heated Steering Wheel", "type": "boolean", "group": "Comfort"},
    {"key": "driver_seat_memory", "label": "Driver Seat Memory", "type": "boolean", "group": "Comfort"},
]


def assemble_features_from_form(form_data) -> dict:
    result = {}
    for feat in FEATURES:
        key = feat["key"]
        if feat["type"] == "boolean":
            result[key] = key in form_data
        else:
            result[key] = form_data.get(key, "")
    return result
