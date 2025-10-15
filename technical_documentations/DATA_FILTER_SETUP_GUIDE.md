# Data Filter Setup Guide - Commercial Employee Profile

## Problem You Discovered:
**User:** fathy  
**Profile:** commercial-employee  
**Issue:** Can see ALL properties but NO leads  
**Goal:** Restrict fathy to see only COMMERCIAL properties

---

## Solution: Add Data Filter for Commercial Properties

### Step-by-Step Instructions:

#### 1. Navigate to Profile Editor
- Go to: **Admin Menu → Manage Profiles**
- Click on **"commercial-employee"** profile card
- Switch to **"Data Filters"** tab

#### 2. Click "Add Filter" Button
- Opens the Data Filter modal

#### 3. Fill in the Form:

**Filter Name:**
```
Commercial Properties Only
```

**Module:**
```
Select: Properties
```

**Description:**
```
Restrict users to see only commercial properties (Office, Retail, Warehouse, etc.)
```

**Model Name:**
```
Property
```

**Filter Type:**
```
Include - Show only matching records
```

**Filter Conditions (JSON):**
```json
{
  "property_type__name__icontains": "commercial"
}
```

**Active:** ✅ Checked  
**Order:** `0`

#### 4. Click "Save Filter"

---

## Understanding the Filter Conditions

### Current Example:
```json
{
  "property_type__name__icontains": "commercial"
}
```

This means: **Show only properties where the property_type name contains "commercial"**

### Other Useful Examples:

#### 1. Filter by Multiple Property Types:
```json
{
  "property_type__name__in": ["Office", "Retail", "Warehouse"]
}
```

#### 2. Filter by Status:
```json
{
  "status": "available",
  "is_deleted": false
}
```

#### 3. Filter by Assigned User:
```json
{
  "assigned_to": "{{ user.id }}"
}
```
(Shows only properties assigned to the logged-in user)

#### 4. Combine Multiple Conditions:
```json
{
  "property_type__name__icontains": "commercial",
  "status": "available",
  "price__gte": 100000
}
```

---

## Why Fathy Sees NO Leads

### Explanation:
The "commercial-employee" profile likely has **NO permissions** set for the **Leads** module.

### How to Fix:

#### Option 1: Enable Leads Module (View Only)
1. Go to profile editor for "commercial-employee"
2. On **"Module Permissions"** tab
3. Find **"Leads"** module
4. Set slider to **Level 1** (View Only)

#### Option 2: Give Full Leads Access
1. Set slider to **Level 2** (View + Create) or higher

#### Option 3: Add Data Filter for Leads Too
If you want fathy to see ONLY commercial leads:

**Module:** Leads  
**Model Name:** Lead  
**Filter Conditions:**
```json
{
  "property_type__icontains": "commercial"
}
```
OR
```json
{
  "assigned_to": "{{ user.id }}"
}
```
(Show only leads assigned to them)

---

## Testing the Configuration

### After Adding the Data Filter:

1. **Logout** from admin account
2. **Login as:** fathy
3. **Navigate to:** Properties module
4. **Verify:** You should ONLY see commercial properties now

### If Still Seeing All Properties:

**Checklist:**
- ✅ Filter is marked as "Active"
- ✅ Filter module is set to "Properties"
- ✅ Model name is exactly "Property" (case-sensitive)
- ✅ JSON syntax is valid (check for commas, quotes)
- ✅ User has logged out and logged back in (session refresh)

---

## Advanced: Field Lookup Syntax

Django ORM field lookups you can use in filter conditions:

| Lookup | Example | Description |
|--------|---------|-------------|
| `__exact` | `"status__exact": "active"` | Exact match |
| `__iexact` | `"name__iexact": "villa"` | Case-insensitive exact |
| `__contains` | `"name__contains": "luxury"` | Contains (case-sensitive) |
| `__icontains` | `"name__icontains": "VILLA"` | Contains (case-insensitive) |
| `__in` | `"id__in": [1, 2, 3]` | In list |
| `__gt` | `"price__gt": 500000` | Greater than |
| `__gte` | `"price__gte": 500000` | Greater than or equal |
| `__lt` | `"price__lt": 1000000` | Less than |
| `__lte` | `"price__lte": 1000000` | Less than or equal |
| `__startswith` | `"code__startswith": "COM"` | Starts with |
| `__istartswith` | `"code__istartswith": "com"` | Starts with (case-insensitive) |
| `__endswith` | `"code__endswith": "001"` | Ends with |
| `__isnull` | `"deleted_at__isnull": true` | Is NULL |

### Relationship Lookups:
```json
{
  "property_type__name": "Office",
  "property_type__category": "Commercial",
  "assigned_to__username": "fathy"
}
```

---

## Quick Reference: Common Filters

### 1. Commercial Properties Only:
```json
{"property_type__name__icontains": "commercial"}
```

### 2. User's Own Records:
```json
{"assigned_to": "{{ user.id }}"}
```

### 3. Active/Available Only:
```json
{"status": "available", "is_deleted": false}
```

### 4. Price Range:
```json
{"price__gte": 100000, "price__lte": 1000000}
```

### 5. Specific Property Types:
```json
{"property_type__id__in": [1, 3, 5, 7]}
```

### 6. Recently Updated:
```json
{"updated_at__gte": "2025-01-01"}
```

---

## Troubleshooting

### Problem: Filter Not Working

**Check:**
1. Is the filter marked as "Active"? ✅
2. Is the user assigned to the correct profile?
3. Did the user logout and login again?
4. Is the JSON syntax valid? (Use JSON validator)
5. Does the field name exist in the model?

### Problem: "Invalid JSON" Error

**Common Mistakes:**
- ❌ Missing quotes: `{property_type: "commercial"}`
- ✅ Correct: `{"property_type": "commercial"}`
- ❌ Trailing comma: `{"status": "active",}`
- ✅ Correct: `{"status": "active"}`
- ❌ Single quotes: `{'status': 'active'}`
- ✅ Correct: `{"status": "active"}`

### Problem: Filter Too Restrictive

If filter shows NO records:
- Check that the filter conditions match EXISTING data
- Test with simpler conditions first
- Use "exclude" type instead of "include"

---

## Next Steps

1. ✅ Add the Commercial Properties filter
2. ✅ Test by logging in as fathy
3. ✅ Add Leads module permission if needed
4. ✅ Optionally add Leads data filter
5. ✅ Configure field-level visibility if needed

**All configuration is now in ONE place: `/profiles/<profile_id>/`**

---

**Need Help?** Check the example buttons in the modal for quick filter templates!
