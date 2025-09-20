# Comprehensive Field Mapping for Granular RBAC System

This document maps every single field, input, dropdown, and form element across all modules for implementing granular field-level permissions.

## Module: Leads (leads.models.Lead)

### 1. BASIC INFORMATION FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `id` | UUIDField | Hidden | Auto | No | N/A |
| `first_name` | CharField | Text Input | Yes | No | N/A |
| `last_name` | CharField | Text Input | Yes | No | N/A |
| `mobile` | CharField | Phone Input | Yes | Yes | N/A |

### 2. CONTACT INFORMATION FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `email` | EmailField | Email Input | No | Yes | N/A |
| `phone` | CharField | Phone Input | No | Yes | N/A |
| `company` | CharField | Text Input | No | No | N/A |
| `title` | CharField | Text Input | No | No | N/A |

### 3. LEAD CLASSIFICATION FIELDS (FOREIGN KEYS)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `lead_type` | ForeignKey | Dropdown | No | No | LeadType.objects.filter(is_active=True) |
| `source` | ForeignKey | Dropdown | No | No | LeadSource.objects.filter(is_active=True) |
| `status` | ForeignKey | Dropdown | No | No | LeadStatus.objects.filter(is_active=True) |
| `priority` | ForeignKey | Dropdown | No | No | LeadPriority.objects.filter(is_active=True) |
| `temperature` | ForeignKey | Dropdown | No | No | LeadTemperature.objects.filter(is_active=True) |

### 4. PROPERTY INTERESTS FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `budget_min` | DecimalField | Number Input | No | Yes | N/A |
| `budget_max` | DecimalField | Number Input | No | Yes | N/A |
| `preferred_locations` | TextField | Textarea | No | No | N/A |
| `property_type` | CharField | Text Input | No | No | N/A |
| `requirements` | TextField | Textarea | No | No | N/A |

### 5. LEAD SCORING FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `score` | IntegerField | Range Input | No | No | N/A (0-100) |

### 6. ASSIGNMENT FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `assigned_to` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |
| `created_by` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |

### 7. COMMUNICATION PREFERENCES
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `preferred_contact_method` | CharField | Radio/Dropdown | No | No | [email, mobile, phone, sms, whatsapp] |
| `best_contact_time` | CharField | Text Input | No | No | N/A |

### 8. TIMESTAMPS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `created_at` | DateTimeField | DateTime | Auto | No | N/A |
| `updated_at` | DateTimeField | DateTime | Auto | No | N/A |
| `last_contacted` | DateTimeField | DateTime | No | No | N/A |
| `next_follow_up` | DateTimeField | DateTime | No | No | N/A |

### 9. CONVERSION TRACKING
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `converted_at` | DateTimeField | DateTime | No | Yes | N/A |
| `conversion_value` | DecimalField | Number Input | No | Yes | N/A |

### 10. ADDITIONAL FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `notes` | TextField | Textarea | No | No | N/A |
| `tags` | CharField | Tags Input | No | No | N/A |
| `is_qualified` | BooleanField | Checkbox | No | No | N/A |

---

## Module: Properties (properties.models.Property)

### 1. PRIMARY IDENTIFICATION
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `property_id` | CharField | Text Input | Yes | No | N/A |
| `property_number` | CharField | Text Input | No | No | N/A |
| `name` | CharField | Text Input | No | No | N/A |

### 2. BASIC PROPERTY INFORMATION
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `building` | CharField | Text Input | No | No | N/A |
| `unit_number` | CharField | Text Input | No | No | N/A |
| `apartment_number` | CharField | Text Input | No | No | N/A |
| `plot_number` | CharField | Text Input | No | No | N/A |
| `floor_number` | IntegerField | Number Input | No | No | N/A |
| `total_floors` | IntegerField | Number Input | No | No | N/A |

### 3. RELATED LOOKUPS (FOREIGN KEYS)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `region` | ForeignKey | Dropdown | No | No | Region.objects.filter(is_active=True) |
| `finishing_type` | ForeignKey | Dropdown | No | No | FinishingType.objects.filter(is_active=True) |
| `unit_purpose` | ForeignKey | Dropdown | No | No | UnitPurpose.objects.filter(is_active=True) |
| `property_type` | ForeignKey | Dropdown | No | No | PropertyType.objects.filter(is_active=True) |
| `category` | ForeignKey | Dropdown | No | No | PropertyCategory.objects.filter(is_active=True) |
| `compound` | ForeignKey | Dropdown | No | No | Compound.objects.filter(is_active=True) |
| `status` | ForeignKey | Dropdown | No | No | PropertyStatus.objects.filter(is_active=True) |
| `activity` | ForeignKey | Dropdown | No | No | PropertyActivity.objects.filter(is_active=True) |
| `project` | ForeignKey | Dropdown | No | No | Project.objects.filter(is_active=True) |
| `currency` | ForeignKey | Dropdown | No | No | Currency.objects.filter(is_active=True) |

### 4. DESCRIPTIVE FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `description` | TextField | Textarea | No | No | N/A |
| `unit_features` | TextField | Textarea | No | No | N/A |
| `phase` | CharField | Text Input | No | No | N/A |
| `the_floors` | TextField | Textarea | No | No | N/A |
| `in_or_outside_compound` | CharField | Text Input | No | No | N/A |
| `year_built` | IntegerField | Number Input | No | No | N/A |

### 5. ROOM INFORMATION
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `rooms` | IntegerField | Number Input | No | No | N/A |
| `living_rooms` | IntegerField | Number Input | No | No | N/A |
| `sales_rooms` | IntegerField | Number Input | No | No | N/A |
| `bathrooms` | IntegerField | Number Input | No | No | N/A |

### 6. AREA MEASUREMENTS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `land_area` | CharField | Text Input | No | No | N/A |
| `land_garden_area` | DecimalField | Number Input | No | No | N/A |
| `sales_area` | DecimalField | Number Input | No | No | N/A |
| `total_space` | DecimalField | Number Input | No | No | N/A |
| `space_earth` | CharField | Text Input | No | No | N/A |
| `space_unit` | CharField | Text Input | No | No | N/A |
| `space_guard` | CharField | Text Input | No | No | N/A |

### 7. PRICING INFORMATION (SENSITIVE)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `base_price` | DecimalField | Number Input | No | Yes | N/A |
| `asking_price` | DecimalField | Number Input | No | Yes | N/A |
| `sold_price` | DecimalField | Number Input | No | Yes | N/A |
| `total_price` | DecimalField | Number Input | No | Yes | N/A |
| `price_per_meter` | DecimalField | Number Input | No | Yes | N/A |
| `transfer_fees` | DecimalField | Number Input | No | Yes | N/A |
| `maintenance_fees` | DecimalField | Number Input | No | Yes | N/A |

### 8. PAYMENT INFORMATION (SENSITIVE)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `down_payment` | DecimalField | Number Input | No | Yes | N/A |
| `installment` | DecimalField | Number Input | No | Yes | N/A |
| `monthly_payment` | DecimalField | Number Input | No | Yes | N/A |
| `payment_frequency` | CharField | Dropdown | No | No | [monthly, quarterly, yearly] |

### 9. FEATURES (JSON FIELDS)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `facilities` | JSONField | Multi-select | No | No | Predefined facility list |
| `features` | JSONField | Multi-select | No | No | Predefined feature list |
| `security_features` | JSONField | Multi-select | No | No | Predefined security list |

### 10. BOOLEAN FEATURES
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `has_garage` | BooleanField | Checkbox | No | No | N/A |
| `garage_type` | CharField | Text Input | No | No | N/A |
| `has_garden` | BooleanField | Checkbox | No | No | N/A |
| `garden_type` | CharField | Text Input | No | No | N/A |
| `has_pool` | BooleanField | Checkbox | No | No | N/A |
| `pool_type` | CharField | Text Input | No | No | N/A |
| `has_terraces` | BooleanField | Checkbox | No | No | N/A |
| `terrace_type` | CharField | Text Input | No | No | N/A |

### 11. STATUS FLAGS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `is_liked` | BooleanField | Checkbox | No | No | N/A |
| `is_in_home` | BooleanField | Checkbox | No | No | N/A |
| `update_required` | BooleanField | Checkbox | No | No | N/A |

### 12. ASSIGNMENT AND MANAGEMENT
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `property_offered_by` | CharField | Text Input | No | No | N/A |
| `handler` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |
| `sales_person` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |
| `last_modified_by` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |
| `assigned_users` | ManyToManyField | Multi-select | No | No | User.objects.filter(is_active=True) |

### 13. CONTACT INFORMATION
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `mobile_number` | CharField | Phone Input | No | Yes | N/A |
| `secondary_phone` | CharField | Phone Input | No | Yes | N/A |
| `telephone` | CharField | Phone Input | No | Yes | N/A |

### 14. OWNER INFORMATION (SENSITIVE)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `owner_name` | CharField | Text Input | No | Yes | N/A |
| `owner_phone` | CharField | Phone Input | No | Yes | N/A |
| `owner_email` | EmailField | Email Input | No | Yes | N/A |
| `owner_notes` | TextField | Textarea | No | Yes | N/A |

### 15. NOTES AND UPDATES
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `notes` | TextField | Textarea | No | No | N/A |
| `sales_notes` | TextField | Textarea | No | No | N/A |
| `general_notes` | TextField | Textarea | No | No | N/A |
| `call_updates` | TextField | Textarea | No | No | N/A |
| `activity_notes` | TextField | Textarea | No | No | N/A |
| `call_update` | TextField | Textarea | No | No | N/A |
| `for_update` | TextField | Textarea | No | No | N/A |

### 16. IMPORTANT DATES
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `last_follow_up` | DateTimeField | DateTime | No | No | N/A |
| `sold_date` | DateField | Date | No | No | N/A |
| `rental_start_date` | DateField | Date | No | No | N/A |
| `rental_end_date` | DateField | Date | No | No | N/A |
| `rent_from` | DateTimeField | DateTime | No | No | N/A |
| `rent_to` | DateTimeField | DateTime | No | No | N/A |

### 17. MEDIA FILES
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `primary_image` | CharField | File Upload | No | No | N/A |
| `thumbnail_path` | CharField | File Upload | No | No | N/A |
| `images` | JSONField | Multi-file Upload | No | No | N/A |
| `property_images` | JSONField | Multi-file Upload | No | No | N/A |
| `videos` | JSONField | Multi-file Upload | No | No | N/A |
| `documents` | JSONField | Multi-file Upload | No | No | N/A |
| `virtual_tour_url` | URLField | URL Input | No | No | N/A |
| `brochure_url` | URLField | URL Input | No | No | N/A |

---

## Module: Projects (projects.models.Project)

### 1. PRIMARY IDENTIFICATION
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `project_id` | CharField | Text Input | Yes | No | N/A |
| `name` | CharField | Text Input | Yes | No | N/A |
| `description` | TextField | Textarea | No | No | N/A |

### 2. LOCATION AND BASIC INFO
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `location` | CharField | Text Input | No | No | N/A |
| `developer` | CharField | Text Input | No | No | N/A |

### 3. STATUS AND CATEGORIZATION
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `status` | ForeignKey | Dropdown | No | No | ProjectStatus.objects.filter(is_active=True) |
| `project_type` | ForeignKey | Dropdown | No | No | ProjectType.objects.filter(is_active=True) |
| `category` | ForeignKey | Dropdown | No | No | ProjectCategory.objects.filter(is_active=True) |
| `priority` | ForeignKey | Dropdown | No | No | ProjectPriority.objects.filter(is_active=True) |

### 4. DATES AND TIMELINE
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `start_date` | DateTimeField | DateTime | No | No | N/A |
| `end_date` | DateTimeField | DateTime | No | No | N/A |
| `completion_year` | IntegerField | Number Input | No | No | N/A |

### 5. UNITS AND CAPACITY
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `total_units` | IntegerField | Number Input | No | No | N/A |
| `available_units` | IntegerField | Number Input | No | No | N/A |

### 6. PRICING (SENSITIVE)
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `price_range` | CharField | Text Input | No | Yes | N/A |
| `currency` | ForeignKey | Dropdown | No | No | Currency.objects.filter(is_active=True) |
| `min_price` | DecimalField | Number Input | No | Yes | N/A |
| `max_price` | DecimalField | Number Input | No | Yes | N/A |

### 7. ASSIGNMENT AND OWNERSHIP
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `assigned_to` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |
| `created_by` | ForeignKey | Dropdown | No | No | User.objects.filter(is_active=True) |

### 8. ADDITIONAL FIELDS
| Field Name | Field Type | Input Type | Required | Sensitive | Dropdown Source |
|------------|------------|------------|----------|-----------|-----------------|
| `notes` | TextField | Textarea | No | No | N/A |
| `tags` | CharField | Tags Input | No | No | N/A |
| `is_active` | BooleanField | Checkbox | No | No | N/A |
| `is_featured` | BooleanField | Checkbox | No | No | N/A |

---

## Permission Profile Examples

### Commercial Property Specialist Profile
**Allowed Fields:**
- Properties: Only `property_type` = 'commercial', `category` = 'commercial'
- Leads: All fields except `budget_max` > 50000
- Projects: All commercial projects only

**Restricted Fields:**
- Properties: `owner_phone`, `owner_email`, `sold_price`
- Leads: High-value budget fields
- Projects: Internal pricing fields

### Residential Property Specialist Profile
**Allowed Fields:**
- Properties: Only `property_type` = 'residential' 
- Leads: All residential-related fields
- Projects: Residential projects only

**Restricted Fields:**
- Properties: Commercial-specific fields
- Leads: Commercial lead sources
- Projects: Commercial project categories

### Junior Sales Agent Profile
**Allowed Fields:**
- Properties: Basic info, no pricing
- Leads: Contact info, basic details
- Projects: View only, no editing

**Restricted Fields:**
- Properties: All pricing fields, owner information
- Leads: Budget information, conversion data
- Projects: Financial information, strategic notes

---

## Implementation Strategy

1. **Field Permission Model**: Track every field with view/edit/create/delete permissions
2. **Dynamic Form Generation**: Forms automatically show/hide fields based on user profile
3. **Dropdown Filtering**: Filter dropdown options based on user profile (e.g., show only commercial property types)
4. **List View Filtering**: Show only relevant columns in list views
5. **Detail View Masking**: Hide sensitive fields in detail views
6. **API Endpoint Filtering**: API responses filtered based on field permissions