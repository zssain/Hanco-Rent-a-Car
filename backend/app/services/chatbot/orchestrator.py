"""
Chatbot Orchestrator Service - State Machine Version
Strict funnel-based conversation flow for Hanco AI
Powered by Gemini AI with fallback
"""

import logging
import httpx
import json
import re
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

from app.core.config import settings
from app.core.firebase import db, Collections

logger = logging.getLogger(__name__)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1/models/"
    "gemini-1.5-flash:generateContent"
)

# State Machine States
STATE_IDLE = "idle"
STATE_VEHICLE_TYPE = "vehicle_type"
STATE_SELECTION = "selection"
STATE_DATES = "dates"
STATE_PICKUP = "pickup"
STATE_DROPOFF = "dropoff"
STATE_INSURANCE = "insurance"
STATE_PAYMENT = "payment"
STATE_QUOTE = "quote"
STATE_CONFIRM = "confirm"
STATE_COMPLETED = "completed"

# State transitions
STATE_MACHINE = {
    STATE_IDLE: STATE_VEHICLE_TYPE,
    STATE_VEHICLE_TYPE: STATE_SELECTION,
    STATE_SELECTION: STATE_DATES,
    STATE_DATES: STATE_PICKUP,
    STATE_PICKUP: STATE_DROPOFF,
    STATE_DROPOFF: STATE_INSURANCE,
    STATE_INSURANCE: STATE_PAYMENT,
    STATE_PAYMENT: STATE_QUOTE,
    STATE_QUOTE: STATE_CONFIRM,
    STATE_CONFIRM: STATE_COMPLETED,
    STATE_COMPLETED: STATE_IDLE,
}

VEHICLE_TYPES = ["economy", "sedan", "suv", "luxury"]
PAYMENT_MODES = ["cash", "card"]


class ChatbotOrchestrator:
    """Chatbot orchestrator with strict state machine"""
    
    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY
    
    async def handle_message(
        self,
        user_message: str,
        session_id: str,
        guest_id: str
    ) -> Dict[str, Any]:
        """
        Handle incoming chat message with state machine logic.
        
        Args:
            user_message: User's message
            session_id: Chat session ID
            guest_id: Guest UUID
            
        Returns:
            Response dict with reply, state, options, etc.
        """
        try:
            # Load or create session
            session = await self._get_or_create_session(session_id, guest_id)
            current_state = session.get('state', STATE_IDLE)
            context = session.get('context', {})
            
            logger.info(f"Session {session_id} in state: {current_state}")
            
            # Process message based on current state
            if current_state == STATE_IDLE:
                response = await self._handle_idle(user_message, context)
            elif current_state == STATE_VEHICLE_TYPE:
                response = await self._handle_vehicle_type(user_message, context)
            elif current_state == STATE_SELECTION:
                response = await self._handle_selection(user_message, context)
            elif current_state == STATE_DATES:
                response = await self._handle_dates(user_message, context)
            elif current_state == STATE_PICKUP:
                response = await self._handle_pickup(user_message, context)
            elif current_state == STATE_DROPOFF:
                response = await self._handle_dropoff(user_message, context)
            elif current_state == STATE_INSURANCE:
                response = await self._handle_insurance(user_message, context)
            elif current_state == STATE_PAYMENT:
                response = await self._handle_payment(user_message, context)
            elif current_state == STATE_QUOTE:
                response = await self._handle_quote(user_message, context)
            elif current_state == STATE_CONFIRM:
                response = await self._handle_confirm(user_message, context, guest_id)
            else:
                response = {
                    'reply': "I'm having trouble. Let's start over. What type of vehicle are you looking for?",
                    'next_state': STATE_VEHICLE_TYPE,
                    'context': {}
                }
            
            # Update session
            await self._update_session(
                session_id,
                response.get('next_state', current_state),
                response.get('context', context)
            )
            
            # Store message
            await self._store_message(session_id, user_message, response['reply'])
            
            return {
                'session_id': session_id,
                'reply': response['reply'],
                'state': response.get('next_state', current_state),
                'options': response.get('options'),
                'data': response.get('data')
            }
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {
                'session_id': session_id,
                'reply': "I encountered an error. Let's start over. What type of vehicle do you need?",
                'state': STATE_VEHICLE_TYPE,
                'options': VEHICLE_TYPES
            }
    
    async def _handle_idle(self, message: str, context: Dict) -> Dict:
        """Handle idle state - start booking flow"""
        # Get available vehicle types from Firebase
        available_types = await self._get_available_vehicle_types()
        
        if not available_types:
            return {
                'reply': "👋 Welcome to Hanco AI! Unfortunately, we don't have any vehicles available at the moment. Please check back later.",
                'next_state': STATE_IDLE,
                'context': {}
            }
        
        types_list = "\n".join([f"• {vtype.title()}" for vtype in available_types])
        
        return {
            'reply': f"👋 Welcome to Hanco AI! I'll help you book the perfect vehicle.\n\nWhat type of vehicle are you looking for?\n\n{types_list}\n\nJust tell me which one interests you!",
            'next_state': STATE_VEHICLE_TYPE,
            'context': {'available_types': available_types},
            'options': available_types
        }
    
    async def _get_available_vehicle_types(self) -> List[str]:
        """Fetch available vehicle categories from Firebase"""
        try:
            categories = set()
            docs = db.collection(Collections.VEHICLES).where('availability_status', '==', 'available').limit(100).stream()
            
            for doc in docs:
                vdata = doc.to_dict()
                category = vdata.get('category', '')
                if category:
                    # Store as-is from database (preserves capitalization)
                    categories.add(category)
            
            return sorted(list(categories))
        except Exception as e:
            logger.error(f"Error fetching vehicle types: {e}")
            return []
    
    async def _handle_vehicle_type(self, message: str, context: Dict) -> Dict:
        """Handle vehicle type selection with Gemini understanding"""
        msg_lower = message.lower()
        available_types = context.get('available_types', [])
        
        # If user asks what's available, show all types
        if any(word in msg_lower for word in ['what', 'which', 'available', 'have', 'show', 'list', 'options']):
            if not available_types:
                available_types = await self._get_available_vehicle_types()
            
            if not available_types:
                return {
                    'reply': "I'm sorry, we don't have any vehicles available at the moment. Please check back later.",
                    'next_state': STATE_IDLE,
                    'context': {}
                }
            
            types_list = "\n".join([f"• **{vtype}**" for vtype in available_types])
            return {
                'reply': f"Here are the vehicle types we currently have available:\n\n{types_list}\n\nWhich type would you like?",
                'next_state': STATE_VEHICLE_TYPE,
                'context': {'available_types': available_types},
                'options': available_types
            }
        
        # Use Gemini to understand which vehicle type user wants
        selected_type = await self._extract_vehicle_type_with_gemini(message, available_types)
        
        if not selected_type:
            # Fallback to case-insensitive keyword matching
            if not available_types:
                available_types = await self._get_available_vehicle_types()
            
            for vtype in available_types or VEHICLE_TYPES:
                if vtype.lower() in msg_lower or msg_lower in vtype.lower():
                    selected_type = vtype  # Use exact database value
                    break
        
        if not selected_type:
            if not available_types:
                available_types = await self._get_available_vehicle_types()
            
            types_list = "\n".join([f"• {vtype}" for vtype in available_types]) if available_types else "• Economy\n• Sedan\n• SUV\n• Luxury"
            
            return {
                'reply': f"I didn't quite catch that. Please choose one of these vehicle types:\n\n{types_list}",
                'next_state': STATE_VEHICLE_TYPE,
                'context': {'available_types': available_types},
                'options': available_types
            }
        
        # Fetch matching vehicles using the exact category value from database
        try:
            vehicles = []
            docs = db.collection(Collections.VEHICLES)\
                .where('category', '==', selected_type)\
                .where('availability_status', '==', 'available')\
                .limit(5)\
                .stream()
            
            for doc in docs:
                vdata = doc.to_dict()
                # Get price from current_price or base_daily_rate
                daily_rate = vdata.get('current_price', vdata.get('base_daily_rate', 0))
                vehicles.append({
                    'id': doc.id,
                    'make': vdata.get('make'),
                    'model': vdata.get('model'),
                    'year': vdata.get('year'),
                    'daily_rate': daily_rate
                })
            
            if not vehicles:
                if not available_types:
                    available_types = await self._get_available_vehicle_types()
                
                types_list = "\n".join([f"• {vtype.title()}" for vtype in available_types]) if available_types else ""
                
                # Build reply message
                reply_msg = f"Sorry, we don't have any **{selected_type.title()}** vehicles available right now.\n\n"
                if types_list:
                    reply_msg += f"Try another category:\n\n{types_list}"
                else:
                    reply_msg += "Please try another category."
                
                return {
                    'reply': reply_msg,
                    'next_state': STATE_VEHICLE_TYPE,
                    'context': {'available_types': available_types},
                    'options': available_types
                }
            
            # Format vehicle list
            vehicle_list = "\n".join([
                f"{i+1}. {v['make']} {v['model']} ({v['year']}) - {v['daily_rate']} SAR/day"
                for i, v in enumerate(vehicles)
            ])
            
            context['vehicle_type'] = selected_type
            context['available_vehicles'] = vehicles
            
            return {
                'reply': f"Great! Here are our available {selected_type} vehicles:\n\n{vehicle_list}\n\nPlease select a vehicle by number (1-{len(vehicles)}):",
                'next_state': STATE_SELECTION,
                'context': context,
                'data': {'vehicles': vehicles}
            }
            
        except Exception as e:
            logger.error(f"Error fetching vehicles: {e}")
            return {
                'reply': "Error loading vehicles. Please try again.",
                'next_state': STATE_VEHICLE_TYPE,
                'context': context
            }
    
    async def _handle_selection(self, message: str, context: Dict) -> Dict:
        """Handle vehicle selection"""
        vehicles = context.get('available_vehicles', [])
        
        if not vehicles:
            return {
                'reply': "Something went wrong. Let's start over. What vehicle type?",
                'next_state': STATE_VEHICLE_TYPE,
                'context': {},
                'options': VEHICLE_TYPES
            }
        
        # Parse selection number
        try:
            selection = int(re.search(r'\d+', message).group())
            if selection < 1 or selection > len(vehicles):
                raise ValueError
            
            selected_vehicle = vehicles[selection - 1]
            context['vehicle_id'] = selected_vehicle['id']
            context['selected_vehicle'] = selected_vehicle
            
            return {
                'reply': f"Perfect! You've selected the {selected_vehicle['make']} {selected_vehicle['model']}.\n\n📅 When do you need it? Please provide your rental dates (e.g., 'Jan 15 to Jan 20' or '2025-01-15 to 2025-01-20'):",
                'next_state': STATE_DATES,
                'context': context
            }
            
        except (AttributeError, ValueError):
            return {
                'reply': f"Please enter a valid number between 1 and {len(vehicles)}:",
                'next_state': STATE_SELECTION,
                'context': context
            }
    
    async def _handle_dates(self, message: str, context: Dict) -> Dict:
        """Handle date selection"""
        start_date, end_date = self._parse_dates(message)
        
        if not start_date or not end_date:
            return {
                'reply': "I couldn't understand those dates. Please provide dates like 'Jan 15 to Jan 20' or '2025-01-15 to 2025-01-20':",
                'next_state': STATE_DATES,
                'context': context
            }
        
        # Validate dates
        if start_date < date.today():
            return {
                'reply': "Start date cannot be in the past. Please provide valid dates:",
                'next_state': STATE_DATES,
                'context': context
            }
        
        if end_date <= start_date:
            return {
                'reply': "End date must be after start date. Please provide valid dates:",
                'next_state': STATE_DATES,
                'context': context
            }
        
        context['start_date'] = start_date.isoformat()
        context['end_date'] = end_date.isoformat()
        duration = (end_date - start_date).days
        context['duration'] = duration
        
        # Fetch branches
        try:
            branches = []
            docs = db.collection(Collections.BRANCHES).where('is_active', '==', True).stream()
            
            for doc in docs:
                bdata = doc.to_dict()
                branches.append({
                    'id': doc.id,
                    'name': bdata.get('name'),
                    'city': bdata.get('city'),
                    'address': bdata.get('address')
                })
            
            context['available_branches'] = branches
            
            branch_list = "\n".join([
                f"{i+1}. {b['name']} ({b['city']}) - {b['address']}"
                for i, b in enumerate(branches)
            ])
            
            return {
                'reply': f"📍 Where would you like to pick up the vehicle?\n\n{branch_list}\n\nSelect pickup location by number:",
                'next_state': STATE_PICKUP,
                'context': context,
                'data': {'branches': branches}
            }
            
        except Exception as e:
            logger.error(f"Error fetching branches: {e}")
            return {
                'reply': "Error loading branch locations. Please try again.",
                'next_state': STATE_DATES,
                'context': context
            }
    
    async def _handle_pickup(self, message: str, context: Dict) -> Dict:
        """Handle pickup branch selection"""
        branches = context.get('available_branches', [])
        
        try:
            selection = int(re.search(r'\d+', message).group())
            if selection < 1 or selection > len(branches):
                raise ValueError
            
            selected_branch = branches[selection - 1]
            context['pickup_branch_id'] = selected_branch['id']
            context['pickup_branch'] = selected_branch
            
            branch_list = "\n".join([
                f"{i+1}. {b['name']} ({b['city']}) - {b['address']}"
                for i, b in enumerate(branches)
            ])
            
            return {
                'reply': f"✅ Pickup: {selected_branch['name']}\n\n📍 Where would you like to drop off the vehicle?\n\n{branch_list}\n\nSelect dropoff location by number:",
                'next_state': STATE_DROPOFF,
                'context': context
            }
            
        except (AttributeError, ValueError):
            return {
                'reply': f"Please enter a valid number between 1 and {len(branches)}:",
                'next_state': STATE_PICKUP,
                'context': context
            }
    
    async def _handle_dropoff(self, message: str, context: Dict) -> Dict:
        """Handle dropoff branch selection"""
        branches = context.get('available_branches', [])
        
        try:
            selection = int(re.search(r'\d+', message).group())
            if selection < 1 or selection > len(branches):
                raise ValueError
            
            selected_branch = branches[selection - 1]
            context['dropoff_branch_id'] = selected_branch['id']
            context['dropoff_branch'] = selected_branch
            
            return {
                'reply': f"✅ Dropoff: {selected_branch['name']}\n\n🛡️ Would you like to add insurance? (15% of subtotal)\n\nReply 'yes' or 'no':",
                'next_state': STATE_INSURANCE,
                'context': context
            }
            
        except (AttributeError, ValueError):
            return {
                'reply': f"Please enter a valid number between 1 and {len(branches)}:",
                'next_state': STATE_DROPOFF,
                'context': context
            }
    
    async def _handle_insurance(self, message: str, context: Dict) -> Dict:
        """Handle insurance selection"""
        msg_lower = message.lower()
        
        if 'yes' in msg_lower or 'sure' in msg_lower or 'ok' in msg_lower:
            insurance_selected = True
        elif 'no' in msg_lower or 'skip' in msg_lower:
            insurance_selected = False
        else:
            return {
                'reply': "Please reply 'yes' or 'no' for insurance:",
                'next_state': STATE_INSURANCE,
                'context': context
            }
        
        context['insurance_selected'] = insurance_selected
        
        return {
            'reply': f"{'✅ Insurance added' if insurance_selected else '❌ No insurance'}\n\n💳 How would you like to pay?\n\nOptions: cash, card",
            'next_state': STATE_PAYMENT,
            'context': context,
            'options': PAYMENT_MODES
        }
    
    async def _handle_payment(self, message: str, context: Dict) -> Dict:
        """Handle payment mode selection"""
        msg_lower = message.lower()
        
        payment_mode = None
        for mode in PAYMENT_MODES:
            if mode in msg_lower:
                payment_mode = mode
                break
        
        if not payment_mode:
            return {
                'reply': "Please choose 'cash' or 'card':",
                'next_state': STATE_PAYMENT,
                'context': context,
                'options': PAYMENT_MODES
            }
        
        context['payment_mode'] = payment_mode
        
        # Calculate pricing
        vehicle = context.get('selected_vehicle', {})
        duration = context.get('duration', 1)
        daily_rate = vehicle.get('daily_rate', 0)
        subtotal = daily_rate * duration
        insurance_amount = subtotal * 0.15 if context.get('insurance_selected') else 0
        total = subtotal + insurance_amount
        
        context['subtotal'] = subtotal
        context['insurance_amount'] = insurance_amount
        context['total_price'] = total
        
        # Format quote
        quote = f"""
📊 **PRICE QUOTE**

🚗 Vehicle: {vehicle.get('make')} {vehicle.get('model')}
📅 Duration: {duration} days ({daily_rate} SAR/day)
💵 Subtotal: {subtotal:.2f} SAR
🛡️ Insurance (15%): {insurance_amount:.2f} SAR
💳 Payment: {payment_mode}

**TOTAL: {total:.2f} SAR**

Would you like to confirm this booking? (yes/no)
"""
        
        return {
            'reply': quote,
            'next_state': STATE_CONFIRM,
            'context': context,
            'data': {
                'quote': {
                    'subtotal': subtotal,
                    'insurance': insurance_amount,
                    'total': total
                }
            }
        }
    
    async def _handle_quote(self, message: str, context: Dict) -> Dict:
        """Handle quote display (should not reach here usually)"""
        return await self._handle_payment(message, context)
    
    async def _handle_confirm(self, message: str, context: Dict, guest_id: str) -> Dict:
        """Handle booking confirmation"""
        msg_lower = message.lower()
        
        if 'yes' in msg_lower or 'confirm' in msg_lower or 'sure' in msg_lower:
            # Create booking
            try:
                booking_id = str(uuid.uuid4())
                booking_data = {
                    'id': booking_id,
                    'guest_id': guest_id,
                    'vehicle_id': context['vehicle_id'],
                    'start_date': context['start_date'],
                    'end_date': context['end_date'],
                    'pickup_branch_id': context['pickup_branch_id'],
                    'dropoff_branch_id': context['dropoff_branch_id'],
                    'insurance_selected': context.get('insurance_selected', False),
                    'insurance_amount': context.get('insurance_amount', 0),
                    'total_price': context.get('total_price', 0),
                    'payment_mode': context.get('payment_mode', 'cash'),
                    'status': 'pending',
                    'payment_status': 'pending',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                
                db.collection(Collections.BOOKINGS).document(booking_id).set(booking_data)
                
                vehicle = context.get('selected_vehicle', {})
                pickup = context.get('pickup_branch', {})
                dropoff = context.get('dropoff_branch', {})
                
                confirmation = f"""
✅ **BOOKING CONFIRMED!**

Booking ID: {booking_id[:8]}

🚗 Vehicle: {vehicle.get('make')} {vehicle.get('model')}
📅 Dates: {context['start_date']} to {context['end_date']}
📍 Pickup: {pickup.get('name')}
📍 Dropoff: {dropoff.get('name')}
💵 Total: {context.get('total_price', 0):.2f} SAR

Thank you for choosing Hanco AI! Your booking is confirmed.

Need anything else? Just say 'hi' to start a new booking.
"""
                
                return {
                    'reply': confirmation,
                    'next_state': STATE_COMPLETED,
                    'context': {},
                    'data': {'booking_id': booking_id}
                }
                
            except Exception as e:
                logger.error(f"Error creating booking: {e}")
                return {
                    'reply': "Sorry, there was an error creating your booking. Please try again later.",
                    'next_state': STATE_IDLE,
                    'context': {}
                }
        
        elif 'no' in msg_lower or 'cancel' in msg_lower:
            return {
                'reply': "Booking cancelled. Would you like to start over? Say 'hi' to begin.",
                'next_state': STATE_IDLE,
                'context': {}
            }
        else:
            return {
                'reply': "Please reply 'yes' to confirm or 'no' to cancel:",
                'next_state': STATE_CONFIRM,
                'context': context
            }
    
    def _parse_dates(self, text: str) -> tuple:
        """Parse date range from text"""
        text = text.lower().replace("–", "-")
        
        # Try common patterns
        if " to " in text:
            parts = text.split(" to ", 1)
        elif " - " in text:
            parts = text.split(" - ", 1)
        else:
            parts = [text]
        
        if len(parts) == 2:
            start = self._parse_single_date(parts[0].strip())
            end = self._parse_single_date(parts[1].strip())
            if start and end:
                return start, end
        
        # Try finding two date patterns
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        dates = re.findall(date_pattern, text)
        if len(dates) >= 2:
            try:
                return date.fromisoformat(dates[0]), date.fromisoformat(dates[1])
            except:
                pass
        
        return None, None
    
    def _parse_single_date(self, text: str) -> Optional[date]:
        """Parse single date from text"""
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%b %d %Y",     # Jan 15 2026
            "%B %d %Y",     # January 15 2026
            "%d %b %Y",     # 15 Jan 2026
            "%d %B %Y",     # 15 January 2026
            "%b %d, %Y",    # Jan 15, 2026
            "%B %d, %Y",    # January 15, 2026
            "%b %d",        # Jan 15 (current year)
            "%B %d",        # January 15 (current year)
            "%d %b",        # 15 Jan (current year)
            "%d %B",        # 15 January (current year)
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(text, fmt)
                # If no year in format, use current year or next year if date passed
                if dt.year == 1900:
                    current_date = date.today()
                    dt = dt.replace(year=current_date.year)
                    # If the date is in the past, assume next year
                    if dt.date() < current_date:
                        dt = dt.replace(year=current_date.year + 1)
                return dt.date()
            except ValueError:
                continue
        
        return None
    
    async def _get_or_create_session(self, session_id: str, guest_id: str) -> Dict:
        """Get or create chat session"""
        try:
            doc = db.collection(Collections.CHAT_SESSIONS).document(session_id).get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                session_data = {
                    'session_id': session_id,
                    'guest_id': guest_id,
                    'state': STATE_IDLE,
                    'context': {},
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                db.collection(Collections.CHAT_SESSIONS).document(session_id).set(session_data)
                return session_data
                
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return {
                'session_id': session_id,
                'guest_id': guest_id,
                'state': STATE_IDLE,
                'context': {}
            }
    
    async def _update_session(self, session_id: str, state: str, context: Dict):
        """Update chat session state"""
        try:
            db.collection(Collections.CHAT_SESSIONS).document(session_id).update({
                'state': state,
                'context': context,
                'updated_at': datetime.utcnow()
            })
        except Exception as e:
            logger.error(f"Error updating session: {e}")
    
    async def _store_message(self, session_id: str, user_message: str, bot_reply: str):
        """Store chat message"""
        try:
            message_id = str(uuid.uuid4())
            message_data = {
                'id': message_id,
                'session_id': session_id,
                'user_message': user_message,
                'bot_reply': bot_reply,
                'timestamp': datetime.utcnow()
            }
            db.collection(Collections.CHAT_MESSAGES).document(message_id).set(message_data)
        except Exception as e:
            logger.error(f"Error storing message: {e}")
    
    async def _extract_vehicle_type_with_gemini(self, message: str, available_types: List[str]) -> Optional[str]:
        """Use Gemini to extract vehicle type from user message"""
        if not self.gemini_api_key:
            return None
        
        try:
            available_str = ", ".join(available_types) if available_types else "economy, sedan, suv, luxury"
            
            prompt = f"""Extract the vehicle category from this user message.

User message: "{message}"

Available categories: {available_str}

Rules:
- Return ONLY the category name in lowercase
- If user mentions multiple categories, return the first one
- If no clear category is mentioned, return "none"
- Common synonyms:
  * "car", "small car", "compact" -> economy
  * "sedan", "medium car", "4-door" -> sedan  
  * "suv", "big car", "family car", "large" -> suv
  * "luxury", "premium", "high-end" -> luxury

Response (one word only):"""

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{GEMINI_API_URL}?key={self.gemini_api_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {
                            "temperature": 0.1,
                            "maxOutputTokens": 20,
                        },
                    },
                )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("candidates"):
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip().lower()
                    # Match case-insensitively and return the exact database value
                    for vtype in (available_types or VEHICLE_TYPES):
                        if text == vtype.lower() or text in vtype.lower() or vtype.lower() in text:
                            return vtype  # Return exact database value (preserves case)
            
            return None
            
        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
            return None


# Global orchestrator instance
orchestrator = ChatbotOrchestrator()
