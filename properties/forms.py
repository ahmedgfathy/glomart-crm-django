from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Property, Region, FinishingType, UnitPurpose, PropertyType, 
    PropertyCategory, Compound, PropertyStatus, PropertyActivity, 
    Project, Currency
)
import uuid


class PropertyCreateForm(forms.ModelForm):
    """Form for creating new properties"""
    
    class Meta:
        model = Property
        fields = [
            'property_number', 'name', 'description',
            'region', 'property_type', 'category', 'compound',
            'status', 'activity', 'project', 'currency',
            'building', 'unit_number', 'apartment_number', 'floor_number',
            'rooms', 'living_rooms', 'sales_rooms', 'bathrooms',
            'total_space', 'sales_area',
            'base_price', 'asking_price', 'total_price',
            'down_payment', 'monthly_payment', 'payment_frequency',
            'mobile_number', 'secondary_phone',
            'owner_name', 'owner_phone', 'owner_email',
            'notes', 'unit_features',
            'has_garage', 'garage_type',
            'has_garden', 'garden_type',
            'has_pool', 'pool_type',
            'has_terraces', 'terrace_type',
        ]
        
        widgets = {
            'property_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter property number'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter property name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter property description'
            }),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'compound': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'project': forms.Select(attrs={'class': 'form-select'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Building name/number'
            }),
            'unit_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unit number'
            }),
            'apartment_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apartment number'
            }),
            'floor_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Floor number'
            }),
            'rooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Number of rooms'
            }),
            'living_rooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
            'sales_rooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
            'bathrooms': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'value': 0
            }),
            'total_space': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Total space in sq meters'
            }),
            'sales_area': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Sales area in sq meters'
            }),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Base price'
            }),
            'asking_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Asking price'
            }),
            'total_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Total price'
            }),
            'down_payment': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Down payment'
            }),
            'monthly_payment': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Monthly payment'
            }),
            'payment_frequency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Monthly, Quarterly'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contact mobile number'
            }),
            'secondary_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Secondary phone number'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property owner name'
            }),
            'owner_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Owner phone number'
            }),
            'owner_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Owner email address'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
            'unit_features': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Unit features and amenities'
            }),
            'has_garage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'garage_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Garage type/details'
            }),
            'has_garden': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'garden_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Garden type/details'
            }),
            'has_pool': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pool_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pool type/details'
            }),
            'has_terraces': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'terrace_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Terrace type/details'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add empty option for select fields
        self.fields['region'].empty_label = "Select a region"
        self.fields['property_type'].empty_label = "Select property type (optional)"
        self.fields['category'].empty_label = "Select category (optional)"
        self.fields['compound'].empty_label = "Select compound (optional)"
        self.fields['status'].empty_label = "Select status (optional)"
        self.fields['activity'].empty_label = "Select activity (optional)"
        self.fields['project'].empty_label = "Select project (optional)"
        self.fields['currency'].empty_label = "Select currency (optional)"
        
        # Set required fields - only essential ones
        required_fields = ['name', 'region', 'owner_name', 'mobile_number']
        
        # Make all fields optional except the required ones
        for field_name, field in self.fields.items():
            if field_name not in required_fields:
                field.required = False
        
        # Ensure required fields are marked as required
        for field_name in required_fields:
            if field_name in self.fields:
                self.fields[field_name].required = True

    def clean_property_number(self):
        """Validate property number uniqueness"""
        property_number = self.cleaned_data.get('property_number')
        if property_number:
            # Check if property number already exists
            if Property.objects.filter(property_number=property_number).exists():
                raise ValidationError("A property with this number already exists.")
        return property_number

    def save(self, commit=True):
        """Save the property with auto-generated property_id"""
        property_obj = super().save(commit=False)
        
        # Generate unique property_id if not set
        if not property_obj.property_id:
            property_obj.property_id = str(uuid.uuid4()).replace('-', '')[:24]
        
        # Set created_by if available (will be set in view)
        if hasattr(self, 'user'):
            property_obj.handler = self.user
            property_obj.last_modified_by = self.user
        
        if commit:
            property_obj.save()
            # Save many-to-many fields
            self.save_m2m()
        
        return property_obj