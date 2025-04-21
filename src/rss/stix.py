from typing import Dict, Optional
from utils.config.project import Project
from classifier import CategoryMatch
import re
from stix2 import Malware, AttackPattern, Relationship, Bundle
import datetime
import json

class StixBuilder:
  def run(self, project: Project, ttps: list[CategoryMatch], capabilities: list[CategoryMatch]) -> str:
    """
    Génère des objets STIX à partir des données du projet et des TTPs/capacités identifiés.
    
    Args:
        project: Le projet contenant les détails du malware
        ttps: Liste des TTPs identifiés (tactiques, techniques, procédures)
        capacities: Liste des capacités du malware identifiées
        
    Returns:
        Bundle STIX contenant tous les objets générés
    """
    stix_objects = []
    
    # Récupération des détails du malware depuis le projet
    malware_details = project['stix_details']
    malware_name = malware_details['name'] if malware_details['name'] else []
    malware_aliases = malware_details['aliases'] if malware_details['aliases'] else []
    is_family = malware_details['is_family']

    # Création de l'objet malware
    malware_obj = Malware(
        name=malware_name,
        is_family=is_family,
        aliases=malware_aliases,
        description=f"Malware {malware_name}",
        capabilities=[capability['name'] for capability in capabilities],
    )
    stix_objects.append(malware_obj)
    
    # Création des attaques (attack patterns) pour chaque TTP
    for ttp in ttps:
        # Extraction des détails sur le TTP
        ttp_name = ttp['name']
        matched_details = ttp.get('details', [])
        description = f"Attack pattern: {ttp_name}"
        
        # Ajout des détails de texte correspondant si disponibles
        if matched_details:
            matched_text = [detail.get('matched_text', '') for detail in matched_details]
            description += f"\n\nDétecté dans le texte: {', '.join(matched_text)}"
        
        attack_pattern = AttackPattern(
            name=ttp_name,
            description=description
        )
        stix_objects.append(attack_pattern)
        
        # Création de la relation liant le TTP au malware
        relationship = Relationship(
            relationship_type="uses",
            source_ref=malware_obj.id,
            target_ref=attack_pattern.id,
            description=f"{malware_name} utilise {ttp_name}"
        )
        stix_objects.append(relationship)
    
    # Regroupement de tous les objets STIX
    stix_bundle = Bundle(objects=stix_objects)

    # Sérialise le bundle en JSON formaté
    return stix_bundle.serialize()
  
