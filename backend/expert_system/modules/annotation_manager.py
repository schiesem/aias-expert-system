"""
annotation_manager.py

Module for managing annotations on graphical elements.
Provides relation discovery, annotation creation/retrieval/deletion.

Annotations are OWL individuals linked to graphical element individuals
via object properties discovered through relation level navigation.
"""

from owlready2 import *
from typing import Dict, List, Optional, Any, Set
import json
import uuid


def _is_class_in_union_or_match(owl_class, domain_or_range_class) -> bool:
    """
    Check if owl_class matches domain_or_range_class, including Union types.

    Handles:
    - Direct class match
    - owl_class is a subclass of domain_or_range_class
    - domain_or_range_class is a Union (Or) containing owl_class or its ancestors
    """
    try:
        # Direct match
        if domain_or_range_class == owl_class:
            return True

        # Check if it's a regular class with descendants
        if hasattr(domain_or_range_class, 'descendants'):
            if owl_class in domain_or_range_class.descendants():
                return True

        # Check if it's a Union (Or) type - owlready2 represents unions as Or objects
        if hasattr(domain_or_range_class, 'Classes'):
            # It's a Union/Or - check each class in the union
            for union_member in domain_or_range_class.Classes:
                if union_member == owl_class:
                    return True
                # Also check if owl_class is a subclass of any union member
                if hasattr(union_member, 'descendants'):
                    if owl_class in union_member.descendants():
                        return True

        # Check if it's a list-like structure (some owlready2 versions)
        if hasattr(domain_or_range_class, '__iter__') and not isinstance(domain_or_range_class, str):
            for member in domain_or_range_class:
                if member == owl_class:
                    return True
                if hasattr(member, 'descendants') and owl_class in member.descendants():
                    return True

    except Exception as e:
        print(f"⚠️ Error checking union membership: {e}")

    return False


# Blacklist for system-level relations that should not appear in annotation UI
# These are for top-level system architecture, not for process-level modeling
RELATION_BLACKLIST = {
    # Properties that should be hidden (regardless of domain/range)
    'properties': [
        'consistsOf',   # AISystem → AIComponent (system structure)
        'hasFunction',  # AIComponent → Function (component structure)
    ],
    # Classes that should be hidden as targets
    'target_classes': [
        'AISystem',     # Top-level container
        'AIComponent',  # Abstract component level
    ],
    # Source classes where the filter does NOT apply
    # When annotating these classes directly, show all relations
    'exempt_source_classes': [
        'AISystem',
        'AIComponent',
    ]
}


class AnnotationManager:
    """
    Manages annotations for graphical elements.

    Annotations are OWL individuals linked to graphical element individuals
    via object properties discovered through relation level navigation.
    """

    def __init__(self, ontology_manager):
        """
        Initialize with reference to OntologyManager.

        Args:
            ontology_manager: Instance of OntologyManager for ontology access
        """
        self.onto_manager = ontology_manager
        self.max_relation_level = 3  # Default depth for relation discovery

    def _is_exempt_from_blacklist(self, owl_class_name: str) -> bool:
        """
        Check if a class is exempt from the relation blacklist.
        Classes like AISystem and AIComponent need access to all their relations.

        Args:
            owl_class_name: Fully qualified class name (e.g., "ISO22989.AISystem")

        Returns:
            True if the class should bypass the blacklist filter
        """
        # Extract short class name (e.g., "AISystem" from "ISO22989.AISystem")
        short_name = owl_class_name.split('.')[-1] if '.' in owl_class_name else owl_class_name
        return short_name in RELATION_BLACKLIST.get('exempt_source_classes', [])

    def _filter_blacklisted_relations(self, relations: List[Dict], owl_class_name: str) -> List[Dict]:
        """
        Filter out blacklisted relations unless the source class is exempt.

        Args:
            relations: List of relation dicts to filter
            owl_class_name: The source class requesting relations

        Returns:
            Filtered list of relations
        """
        # If source class is exempt, return all relations unfiltered
        if self._is_exempt_from_blacklist(owl_class_name):
            print(f"   ℹ️ Class {owl_class_name} is exempt from blacklist filter")
            return relations

        blacklisted_props = RELATION_BLACKLIST.get('properties', [])
        blacklisted_targets = RELATION_BLACKLIST.get('target_classes', [])

        filtered = []
        for rel in relations:
            prop_name = rel.get('property', '')
            target_class = rel.get('target_class', '')
            # Extract short class name for comparison
            target_short = target_class.split('.')[-1] if '.' in target_class else target_class

            # Check if property is blacklisted
            if prop_name in blacklisted_props:
                print(f"   🚫 Filtering out blacklisted property: {prop_name}")
                continue

            # Check if target class is blacklisted
            if target_short in blacklisted_targets:
                print(f"   🚫 Filtering out blacklisted target class: {target_class}")
                continue

            filtered.append(rel)

        if len(filtered) < len(relations):
            print(f"   → Filtered {len(relations) - len(filtered)} blacklisted relations")

        return filtered

    def get_relation_level_1(self, owl_class_name: str, include_incoming: bool = True) -> List[Dict[str, Any]]:
        """
        Get all object properties (relations) directly defined for a class.
        Includes both outgoing relations (class is in domain) and incoming relations (class is in range).

        Args:
            owl_class_name: Fully qualified class name (e.g., "ISO22989.Training")
            include_incoming: If True, also include incoming relations (default True)

        Returns:
            List of dicts with:
            - property: property name
            - target_class: target class name (for outgoing) or source_class (for incoming)
            - cardinality: cardinality restriction (e.g., "1..1", "0..*")
            - level: 1
            - is_required: True if min cardinality > 0
            - direction: "outgoing" or "incoming"
        """
        relations = []

        try:
            # Get the OWL class
            owl_class = self.onto_manager.get_class_by_name(owl_class_name)
            if not owl_class:
                print(f"⚠️ Class {owl_class_name} not found")
                return []

            # Get the world and ontology
            world = self.onto_manager.world
            onto = self.onto_manager.ontology

            # ========================================
            # OUTGOING RELATIONS (class is in domain)
            # ========================================
            for prop in world.object_properties():
                # Check if this property has domain restrictions for our class
                has_domain = False

                if prop.domain:
                    for domain_class in prop.domain:
                        # Handle different types of domain restrictions including Unions
                        try:
                            if _is_class_in_union_or_match(owl_class, domain_class):
                                has_domain = True
                                break
                        except Exception as e:
                            # If we can't determine domain, skip this domain_class
                            print(f"⚠️ Could not check domain for {prop.name}: {e}")
                            continue
                else:
                    # No domain restriction means it can be used with any class
                    has_domain = True

                if has_domain:
                    # Get range (target classes)
                    raw_target_classes = prop.range if prop.range else []

                    if not raw_target_classes:
                        # No range specified, skip
                        continue

                    # Expand Union types in range to individual classes
                    target_classes = []
                    for tc in raw_target_classes:
                        # Check if it's a Union (Or) type
                        if hasattr(tc, 'Classes'):
                            # It's a Union - add each member
                            target_classes.extend(tc.Classes)
                        else:
                            target_classes.append(tc)

                    for target_class in target_classes:
                        # Get target class name (skip complex restrictions)
                        target_class_name = self._get_class_full_name(target_class)
                        if not target_class_name:
                            # Skip complex restrictions (Or, And, etc.)
                            continue

                        # Get cardinality restrictions
                        cardinality = self._get_cardinality(owl_class, prop)
                        is_required = cardinality.get('min', 0) > 0

                        # Add the base target class
                        relations.append({
                            'property': prop.name,
                            'target_class': target_class_name,
                            'cardinality': self._format_cardinality(cardinality),
                            'level': 1,
                            'is_required': is_required,
                            'description': self._get_property_description(prop),
                            'direction': 'outgoing'
                        })

                        # Also add all subclasses of the target class as valid targets
                        # This allows annotating with more specific types (e.g., Data instead of DataUnit)
                        if hasattr(target_class, 'descendants'):
                            for subclass in target_class.descendants():
                                # Skip the class itself (already added above)
                                if subclass == target_class:
                                    continue
                                subclass_name = self._get_class_full_name(subclass)
                                if subclass_name:
                                    relations.append({
                                        'property': prop.name,
                                        'target_class': subclass_name,
                                        'cardinality': self._format_cardinality(cardinality),
                                        'level': 1,
                                        'is_required': False,  # Subclasses are alternatives, not required
                                        'description': self._get_property_description(prop),
                                        'direction': 'outgoing',
                                        'is_subclass_of': target_class_name  # Mark as subclass option
                                    })

            # ========================================
            # INCOMING RELATIONS (class is in range)
            # ========================================
            if include_incoming:
                incoming_relations = self._get_incoming_relations(owl_class, world)
                relations.extend(incoming_relations)

            print(f"✅ Found {len(relations)} relations for {owl_class_name} (outgoing + incoming)")

            # ========================================
            # APPLY BLACKLIST FILTER
            # ========================================
            relations = self._filter_blacklisted_relations(relations, owl_class_name)

            return relations

        except Exception as e:
            print(f"❌ Error getting relations for {owl_class_name}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_incoming_relations(self, owl_class, world) -> List[Dict[str, Any]]:
        """
        Get all incoming relations where this class is in the range (target).

        For example, if owl_class is "Inference" and there's a property "executes"
        with domain "MLModel" and range "Inference", this will return:
        { property: "executes", source_class: "MLModel", direction: "incoming" }

        Args:
            owl_class: The OWL class to find incoming relations for
            world: The owlready2 world

        Returns:
            List of incoming relation dicts
        """
        incoming_relations = []

        try:
            for prop in world.object_properties():
                # Check if this property has range that includes our class (including Unions)
                has_range = False

                if prop.range:
                    for range_class in prop.range:
                        try:
                            if _is_class_in_union_or_match(owl_class, range_class):
                                has_range = True
                                break
                        except Exception as e:
                            print(f"⚠️ Could not check range for {prop.name}: {e}")
                            continue

                if has_range:
                    # Get domain (source classes) for incoming relation
                    raw_source_classes = prop.domain if prop.domain else []

                    if not raw_source_classes:
                        # No domain specified, skip (can't determine source)
                        continue

                    # Expand Union types in domain to individual classes
                    source_classes = []
                    for sc in raw_source_classes:
                        if hasattr(sc, 'Classes'):
                            # It's a Union - add each member
                            source_classes.extend(sc.Classes)
                        else:
                            source_classes.append(sc)

                    for source_class in source_classes:
                        # Get source class name (skip complex restrictions)
                        source_class_name = self._get_class_full_name(source_class)
                        if not source_class_name:
                            continue

                        # Get cardinality (from source class perspective)
                        cardinality = self._get_cardinality(source_class, prop)
                        is_required = cardinality.get('min', 0) > 0

                        incoming_relations.append({
                            'property': prop.name,
                            'source_class': source_class_name,  # The class that points TO us
                            'target_class': source_class_name,  # For UI compatibility (shows what we connect to)
                            'cardinality': self._format_cardinality(cardinality),
                            'level': 1,
                            'is_required': is_required,
                            'description': self._get_property_description(prop),
                            'direction': 'incoming'
                        })

            print(f"   → Found {len(incoming_relations)} incoming relations")
            return incoming_relations

        except Exception as e:
            print(f"❌ Error getting incoming relations: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_cardinality(self, owl_class, prop) -> Dict[str, int]:
        """Extract cardinality restrictions from class restrictions."""
        cardinality = {'min': 0, 'max': None}  # None = unlimited

        try:
            # Check class restrictions
            for restriction in owl_class.is_a:
                if isinstance(restriction, Restriction):
                    if restriction.property == prop:
                        if hasattr(restriction, 'cardinality'):
                            cardinality['min'] = restriction.cardinality
                            cardinality['max'] = restriction.cardinality
                        elif hasattr(restriction, 'min_cardinality'):
                            cardinality['min'] = restriction.min_cardinality
                        elif hasattr(restriction, 'max_cardinality'):
                            cardinality['max'] = restriction.max_cardinality
        except Exception as e:
            print(f"⚠️ Error getting cardinality: {e}")

        return cardinality

    def _format_cardinality(self, cardinality: Dict[str, int]) -> str:
        """Format cardinality dict as string (e.g., '1..1', '0..*')."""
        min_val = cardinality.get('min', 0)
        max_val = cardinality.get('max', None)

        if max_val is None:
            return f"{min_val}..*"
        else:
            return f"{min_val}..{max_val}"

    def _get_class_full_name(self, owl_class) -> str:
        """Get fully qualified class name including namespace."""
        try:
            # Skip complex restrictions (Or, And, Not, etc.)
            if not hasattr(owl_class, 'name'):
                return None

            if hasattr(owl_class, 'namespace') and owl_class.namespace:
                namespace_name = owl_class.namespace.name
                if namespace_name:
                    return f"{namespace_name}.{owl_class.name}"
            return owl_class.name
        except Exception as e:
            print(f"⚠️ Error getting class full name: {e}")
            return None

    def _get_property_description(self, prop) -> str:
        """Get property description from annotation if available."""
        try:
            if hasattr(prop, 'comment') and prop.comment:
                return prop.comment[0] if isinstance(prop.comment, list) else prop.comment
        except Exception as e:
            pass
        return ""

    def is_graphical_class(self, class_name: str) -> bool:
        """
        Check if a class represents a graphical element (node or edge).

        Graphical classes are those that inherit from:
        - Function (and subclasses like Inference, Training, etc.)
        - Resource (and subclasses like Dataset, Model, etc.)
        - Product (and subclasses)
        - Assignment (edge type)
        - Flow (edge type)
        - Communication (edge type)

        Args:
            class_name: Fully qualified class name (e.g., "ISO22989.Prediction")

        Returns:
            True if the class should be represented graphically, False otherwise
        """
        try:
            # Get the OWL class
            owl_class = self.onto_manager.get_class_by_name(class_name)
            if not owl_class:
                return False

            # Define base graphical classes
            graphical_base_classes = {
                'Function', 'Product', 'Resource',  # Node types
                'Assignment', 'Flow', 'Communication',  # Edge types
            }

            # Check if this class or any ancestor is a graphical base class
            for ancestor in owl_class.ancestors():
                if hasattr(ancestor, 'name') and ancestor.name in graphical_base_classes:
                    return True

            return False

        except Exception as e:
            print(f"⚠️ Error checking if class is graphical: {e}")
            return False

    def get_relation_level_n(
        self,
        owl_class_name: str,
        max_level: int = 3,
        current_level: int = 1,
        visited: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Recursively discover relations up to max_level depth.
        Handles both outgoing and incoming relations.

        Args:
            owl_class_name: Starting class name
            max_level: Maximum depth to explore (default 3)
            current_level: Current recursion level
            visited: Set of already visited classes (prevents cycles)

        Returns:
            List of all relations up to max_level, with level indicator
        """
        if visited is None:
            visited = set()

        # Prevent cycles
        if owl_class_name in visited or current_level > max_level:
            return []

        visited.add(owl_class_name)

        # Get level 1 relations for this class (includes both outgoing and incoming)
        relations = self.get_relation_level_1(owl_class_name)
        all_relations = relations.copy()

        # Recursively get next levels
        if current_level < max_level:
            for relation in relations:
                # For outgoing relations: follow target_class
                # For incoming relations: follow source_class (stored in target_class for UI compatibility)
                next_class = relation['target_class']

                # Get relations for the next class
                next_level_relations = self.get_relation_level_n(
                    next_class,
                    max_level,
                    current_level + 1,
                    visited.copy()  # Use copy to allow same class in different paths
                )

                # Mark with correct level and parent
                for next_rel in next_level_relations:
                    next_rel['level'] = current_level + 1
                    next_rel['parent_class'] = next_class  # Immediate parent, not the root
                    next_rel['parent_property'] = relation['property']
                    next_rel['parent_direction'] = relation.get('direction', 'outgoing')

                all_relations.extend(next_level_relations)

        return all_relations

    def create_annotation(
        self,
        element_id: str,
        element_class_name: str,
        relation_property: str,
        target_class_name: str,
        instance_data: Dict[str, Any],
        parent_instance_name: Optional[str] = None,
        direction: str = "outgoing"
    ) -> Optional[Thing]:
        """
        Create an annotation instance and link it to a graphical element or parent instance.

        Args:
            element_id: ID of the graphical element (e.g., "Training1")
            element_class_name: OWL class of the graphical element (e.g., "Training")
            relation_property: Object property name to use for linking
            target_class_name: OWL class to instantiate
            instance_data: Dict with 'name' and optional 'properties'
            parent_instance_name: Optional parent instance name for nested annotations (Level 2+)
            direction: "outgoing" (element --property--> new_instance) or
                       "incoming" (new_instance --property--> element)

        Returns:
            Created OWL individual or None if failed

        Example:
            # Outgoing annotation: Inference -> creates -> Prediction
            create_annotation(
                element_id="Inference1",
                relation_property="creates",
                target_class_name="ISO22989.Prediction",
                instance_data={'name': 'MyPrediction'},
                direction="outgoing"
            )

            # Incoming annotation: MLModel -> executes -> Inference
            create_annotation(
                element_id="Inference1",
                relation_property="executes",
                target_class_name="ISO22989.MLModel",
                instance_data={'name': 'MyModel'},
                direction="incoming"
            )
        """
        try:
            print(f"🔧 Creating {'incoming' if direction == 'incoming' else 'outgoing'} annotation for {element_id}...")

            # Determine the element individual (element or parent instance)
            if parent_instance_name:
                # Level 2+: Link to parent instance
                element_individual = self.onto_manager.get_individual_by_name(parent_instance_name)
                if not element_individual:
                    raise ValueError(f"Parent instance {parent_instance_name} not found in ontology")
                print(f"   Linking to parent instance: {parent_instance_name}")
            else:
                # Level 1: Link to graphical element (create if doesn't exist)
                element_individual = self.onto_manager.get_individual_by_name(element_id)
                if not element_individual:
                    print(f"📝 Element {element_id} not found, creating it as {element_class_name}")

                    # Get the element's class
                    element_class = self.onto_manager.get_class_by_name(element_class_name)
                    if not element_class:
                        raise ValueError(f"Element class {element_class_name} not found in ontology")

                    # Create the element individual with explicit namespace
                    onto = self.onto_manager.ontology
                    with onto:
                        element_individual = element_class(element_id, namespace=onto)
                    print(f"✅ Created element individual: {element_id} ({element_class_name})")

            # Get the target class (class to instantiate)
            target_class = self.onto_manager.get_class_by_name(target_class_name)
            if not target_class:
                raise ValueError(f"Class {target_class_name} not found")

            # Get user-provided display name and generate random ID
            display_name = instance_data.get('name')
            if not display_name:
                raise ValueError("Instance name is required")

            # Generate random 8-character ID for the OWL individual
            instance_id = str(uuid.uuid4())[:8]

            # Create new instance with random ID and explicit namespace
            onto = self.onto_manager.ontology
            with onto:
                annotation_instance = target_class(instance_id, namespace=onto)
            print(f"✅ Created new instance: {instance_id}")

            # Set hasName property with user's display name
            annotation_instance.hasName = [display_name]
            print(f"  ✓ Set hasName = {display_name}")

            # Set datatype properties
            properties = instance_data.get('properties', {})
            for prop_name, prop_value in properties.items():
                if hasattr(annotation_instance, prop_name):
                    setattr(annotation_instance, prop_name, prop_value)
                    print(f"  ✓ Set {prop_name} = {prop_value}")

            # Link via object property
            object_property = self.onto_manager.get_property_by_name(relation_property)
            if not object_property:
                raise ValueError(f"Property {relation_property} not found")

            # Determine source and target based on direction
            if direction == "incoming":
                # Incoming: new_instance --property--> element
                # Example: MLModel --executes--> Inference
                source_individual = annotation_instance
                target_individual = element_individual
                print(f"🔗 Linking elements (INCOMING)...")
                print(f"   Property: {object_property} ({type(object_property)})")
                print(f"   From (new): {annotation_instance} ({annotation_instance.__class__})")
                print(f"   To (element): {element_individual} ({element_individual.__class__})")
            else:
                # Outgoing: element --property--> new_instance
                # Example: Inference --creates--> Prediction
                source_individual = element_individual
                target_individual = annotation_instance
                print(f"🔗 Linking elements (OUTGOING)...")
                print(f"   Property: {object_property} ({type(object_property)})")
                print(f"   From (element): {element_individual} ({element_individual.__class__})")
                print(f"   To (new): {annotation_instance} ({annotation_instance.__class__})")

            # Add the link using owlready2 property syntax
            try:
                # In owlready2, use property_object[individual] to get the value list
                prop_list = object_property[source_individual]
                print(f"   Property list before: {list(prop_list)}")

                if target_individual not in prop_list:
                    prop_list.append(target_individual)
                    print(f"   Property list after: {list(prop_list)}")
                    source_name = parent_instance_name if parent_instance_name else element_id
                    if direction == "incoming":
                        print(f"✅ Linked {instance_id} (hasName: {display_name}) --{relation_property}--> {source_name}")
                    else:
                        print(f"✅ Linked {source_name} --{relation_property}--> {instance_id} (hasName: {display_name})")
                else:
                    print(f"ℹ️ Link already exists")

            except Exception as e:
                print(f"❌ Error during linking: {e}")
                import traceback
                traceback.print_exc()
                raise

            # Verify source individual has properties before saving
            all_props = list(source_individual.get_properties())
            print(f"🔍 {source_individual.name} now has {len(all_props)} properties:")
            for prop in all_props:
                if isinstance(prop, ObjectPropertyClass):
                    values = getattr(source_individual, prop.name, [])
                    print(f"   - {prop.name}: {values}")

            # Save ontology
            self.onto_manager.save_ontology()

            return annotation_instance

        except Exception as e:
            print(f"❌ Error creating annotation: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_annotations(
        self,
        element_id: str,
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Get all annotations for a graphical element.
        Includes both outgoing annotations (element --> annotation)
        and incoming annotations (annotation --> element).

        Args:
            element_id: ID of the graphical element
            max_depth: Maximum depth to traverse annotation graph

        Returns:
            Nested dict structure with annotations at each level
        """
        try:
            element_individual = self.onto_manager.get_individual_by_name(element_id)
            if not element_individual:
                print(f"⚠️ Element {element_id} not found")
                return {}

            # Get outgoing annotations (element --> annotation)
            outgoing = self._traverse_annotations(element_individual, max_depth)

            # Get incoming annotations (annotation --> element)
            incoming = self._get_incoming_annotations(element_individual, max_depth)

            # Merge outgoing and incoming
            # Mark incoming annotations with direction
            for prop_name, prop_values in incoming.items():
                incoming_key = f"{prop_name}__incoming"
                outgoing[incoming_key] = prop_values

            annotations = {
                'element_id': element_id,
                'element_class': self._get_class_full_name(element_individual.__class__),
                'annotations': outgoing
            }

            # Debug logging
            print(f"📊 Retrieved annotations for {element_id}:")
            print(f"   Element class: {annotations['element_class']}")
            print(f"   Annotation properties found: {list(outgoing.keys())}")
            for prop_name, prop_values in outgoing.items():
                direction = "incoming" if "__incoming" in prop_name else "outgoing"
                print(f"   - {prop_name} ({direction}): {len(prop_values)} instance(s)")
                for val in prop_values:
                    print(f"     → {val['name']} ({val['class']})")

            return annotations

        except Exception as e:
            print(f"❌ Error getting annotations: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _get_incoming_annotations(
        self,
        element_individual: Thing,
        max_depth: int
    ) -> Dict[str, List[Dict]]:
        """
        Get all incoming annotations (annotations that point TO this element).

        For example, if element is "Inference1" and there's an MLModel instance
        with "executes" property pointing to "Inference1", this will return:
        { "executes": [{ name: "MLModel1", class: "MLModel", direction: "incoming" }] }

        Args:
            element_individual: The OWL individual to find incoming annotations for
            max_depth: Maximum depth to traverse (for sub-annotations of incoming)

        Returns:
            Dict mapping property names to lists of incoming annotation data
        """
        incoming = {}

        try:
            # Iterate through ALL individuals in the ontology
            for individual in self.onto_manager.ontology.individuals():
                # Skip the element itself
                if individual == element_individual:
                    continue

                # Check all object properties of this individual
                for prop in individual.get_properties():
                    if not isinstance(prop, ObjectPropertyClass):
                        continue

                    values = getattr(individual, prop.name, [])
                    if not isinstance(values, list):
                        values = [values] if values else []

                    # Check if this individual points to our element
                    if element_individual in values:
                        print(f"   ← Found incoming: {individual.name} --{prop.name}--> {element_individual.name}")

                        # Build annotation data
                        annotation_data = {
                            'name': individual.name,
                            'class': self._get_class_full_name(individual.__class__),
                            'properties': self._get_datatype_properties(individual),
                            'direction': 'incoming'
                        }

                        # Get sub-annotations for the incoming individual (its outgoing properties)
                        if max_depth > 1:
                            annotation_data['sub_annotations'] = self._traverse_annotations(
                                individual, max_depth, current_depth=2, visited=set(), path=[element_individual.name]
                            )

                        # Add to result
                        if prop.name not in incoming:
                            incoming[prop.name] = []
                        incoming[prop.name].append(annotation_data)

            print(f"   → Found {sum(len(v) for v in incoming.values())} total incoming annotations")
            return incoming

        except Exception as e:
            print(f"⚠️ Error getting incoming annotations: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _traverse_annotations(
        self,
        individual: Thing,
        max_depth: int,
        current_depth: int = 1,
        visited: Optional[Set[str]] = None,
        path: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Recursively traverse annotation graph."""
        if visited is None:
            visited = set()
        if path is None:
            path = []

        individual_name = individual.name

        # Check for cycles (same individual in current path)
        if individual_name in path:
            print(f"⚠️ Cycle detected at {individual_name}, stopping traversal")
            return {}

        # Check max depth
        if current_depth > max_depth:
            return {}

        # Add to current path for cycle detection
        current_path = path + [individual_name]
        visited.add(individual_name)
        result = {}

        try:
            # Debug: List all properties
            all_props = list(individual.get_properties())
            print(f"🔍 Traversing {individual_name}: found {len(all_props)} total properties")

            # Get all object properties
            object_props = [p for p in all_props if isinstance(p, ObjectPropertyClass)]
            print(f"   → {len(object_props)} object properties: {[p.name for p in object_props]}")

            for prop in object_props:
                values = getattr(individual, prop.name, [])
                if not isinstance(values, list):
                    values = [values] if values else []

                print(f"   → Property '{prop.name}' has {len(values)} value(s)")

                prop_annotations = []
                for value in values:
                    if value:
                        print(f"      → Value: {value.name} ({value.__class__})")
                        # Get datatype properties of this individual
                        value_data = {
                            'name': value.name,
                            'class': self._get_class_full_name(value.__class__),
                            'properties': self._get_datatype_properties(value)
                        }

                        # Recursively get sub-annotations
                        if current_depth < max_depth:
                            value_data['sub_annotations'] = self._traverse_annotations(
                                value, max_depth, current_depth + 1, visited, current_path
                            )

                        prop_annotations.append(value_data)

                if prop_annotations:
                    result[prop.name] = prop_annotations
        except Exception as e:
            print(f"⚠️ Error traversing annotations: {e}")
            import traceback
            traceback.print_exc()

        return result

    def _get_datatype_properties(self, individual: Thing) -> Dict[str, Any]:
        """Get all datatype property values for an individual."""
        properties = {}

        try:
            for prop in individual.get_properties():
                if isinstance(prop, DataPropertyClass):
                    value = getattr(individual, prop.name, None)
                    if value is not None:
                        properties[prop.name] = value
        except Exception as e:
            print(f"⚠️ Error getting datatype properties: {e}")

        return properties

    def delete_annotation(
        self,
        element_id: str,
        relation_property: str,
        annotation_id: str,
        direction: str = "outgoing"
    ) -> bool:
        """
        Delete an annotation from a graphical element.

        Args:
            element_id: ID of the graphical element
            relation_property: Property linking to the annotation
            annotation_id: Random ID of the annotation instance to delete
            direction: "outgoing" (element --> annotation) or "incoming" (annotation --> element)

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🗑️ Deleting {'incoming' if direction == 'incoming' else 'outgoing'} annotation {annotation_id} from {element_id}...")

            element_individual = self.onto_manager.get_individual_by_name(element_id)
            if not element_individual:
                print(f"⚠️ Element {element_id} not found")
                return False

            annotation_individual = self.onto_manager.get_individual_by_name(annotation_id)
            if not annotation_individual:
                print(f"⚠️ Annotation {annotation_id} not found")
                return False

            # Determine source and target based on direction
            if direction == "incoming":
                # Incoming: annotation --property--> element
                # So the link is FROM annotation TO element
                source_individual = annotation_individual
                target_individual = element_individual
                print(f"   Removing incoming link: {annotation_id} --{relation_property}--> {element_id}")
            else:
                # Outgoing: element --property--> annotation
                source_individual = element_individual
                target_individual = annotation_individual
                print(f"   Removing outgoing link: {element_id} --{relation_property}--> {annotation_id}")

            # Remove the link
            current_values = getattr(source_individual, relation_property, [])
            if not isinstance(current_values, list):
                current_values = [current_values] if current_values else []

            if target_individual in current_values:
                current_values.remove(target_individual)
                setattr(source_individual, relation_property, current_values)
                print(f"✅ Removed link successfully")
            else:
                print(f"⚠️ Link not found in property values")

            # Optionally delete the annotation instance itself
            # (only if no other elements reference it)
            if not self._is_referenced_elsewhere(annotation_individual, element_individual):
                destroy_entity(annotation_individual)
                print(f"🗑️ Deleted instance: {annotation_id}")
            else:
                print(f"ℹ️ Instance {annotation_id} still referenced elsewhere, keeping it")

            self.onto_manager.save_ontology()
            return True

        except Exception as e:
            print(f"❌ Error deleting annotation: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _is_referenced_elsewhere(
        self,
        annotation_individual: Thing,
        excluding_individual: Thing
    ) -> bool:
        """Check if an annotation is referenced by other individuals."""
        try:
            # Get all individuals that reference this annotation
            for individual in self.onto_manager.ontology.individuals():
                if individual == excluding_individual:
                    continue

                for prop in individual.get_properties():
                    if isinstance(prop, ObjectPropertyClass):
                        values = getattr(individual, prop.name, [])
                        if not isinstance(values, list):
                            values = [values] if values else []

                        if annotation_individual in values:
                            return True
        except Exception as e:
            print(f"⚠️ Error checking references: {e}")

        return False

    def get_annotation_count(self, element_id: str) -> int:
        """
        Get count of annotations for an element.

        Args:
            element_id: ID of the graphical element

        Returns:
            Count of top-level annotations
        """
        try:
            annotations = self.get_annotations(element_id, max_depth=1)
            return len(annotations.get('annotations', {}))
        except Exception as e:
            print(f"❌ Error getting annotation count: {e}")
            return 0
