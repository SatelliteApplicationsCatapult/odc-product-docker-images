import uuid
from datetime import datetime
import yaml

def generate_datacube_metadata(metadata_obj_key,
                               bands,
                               band_base_name,
                               product_type,
                               platform,
                               instrument,
                               time_from, time_to,
                               longitude_from, longitude_to,
                               latitude_from, latitude_to,
                               output_crs,
                               x_from, x_to,
                               y_from, y_to,
                               **kwargs):
    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, metadata_obj_key)),
        'image': {
            'bands': {
                band: {
                    'path': f"{band_base_name}_{band}.tif"
                } for band in bands
            }
        },
        'extent': {
            'coord': {
                'll': {
                    'lat': float(latitude_from),
                    'lon': float(longitude_from)
                },
                'lr': {
                    'lat': float(latitude_from),
                    'lon': float(longitude_to)
                },
                'ul': {
                    'lat': float(latitude_to),
                    'lon': float(longitude_from)
                },
                'ur': {
                    'lat': float(latitude_to),
                    'lon': float(longitude_to)
                }
            },
            'to_dt': f"{time_to}",
            'from_dt': f"{time_from}",
            'center_dt': f"{time_to}"
        },
        'format': {
            'name': 'GeoTIFF'
        },
        'lineage': {
            'source_datasets': {}
        },
        'platform': {
            'code': f"{platform}"
        },
        'instrument': {
            'name': f"{instrument}"
        },
        'statistics': {
            'step': '1y',
            'period': '1y'
        },
        'creation_dt': datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        'grid_spatial': {
            'projection': {
                'geo_ref_points': {
                    'll': {
                        'x': float(x_from),
                        'y': float(y_from)
                    },
                    'lr': {
                        'x': float(x_to),
                        'y': float(y_from)
                    },
                    'ul': {
                        'x': float(x_from),
                        'y': float(y_to)
                    },
                    'ur': {
                        'x': float(x_to),
                        'y': float(y_to)
                    }
                },
                'spatial_reference': f"{output_crs}"
            }
        },
        'product_type': f"{product_type}"
    }

    return doc
