import json
import re
from typing import List, Dict, Any, Optional
import os

class AgenticDocumentExtractor:
    def __init__(self, api_key: str):
        from openai import OpenAI
        # Limpiar cualquier configuración global que pueda causar problemas
        import os
        # Remover variables de entorno de proxy si existen
        for key in list(os.environ.keys()):
            if 'proxy' in key.lower():
                del os.environ[key]
        
        # Crear cliente sin argumentos adicionales
        self.client = OpenAI(api_key=api_key)
        
    def extract_transactions(self, text: str, bank_name: str = "Unknown") -> List[Dict[str, Any]]:
        """
        Extract transactions using agentic approach with OpenAI.
        This method uses a more intelligent prompt that adapts to any document format.
        """
        if not text.strip():
            return []
            
        # Split text into manageable chunks if too long
        chunks = self._split_text_into_chunks(text, max_tokens=12000)
        
        all_transactions = []
        
        for i, chunk in enumerate(chunks):
            print(f"🤖 Procesando chunk {i+1}/{len(chunks)} con extractor agéntico...")
            
            try:
                chunk_transactions = self._process_chunk_agentic(chunk, bank_name, i+1, len(chunks))
                all_transactions.extend(chunk_transactions)
            except Exception as e:
                print(f"❌ Error procesando chunk {i+1} con extractor agéntico: {e}")
                continue
                
        # Remove duplicates and validate
        unique_transactions = self._deduplicate_transactions(all_transactions)
        print(f"📊 Total de transacciones extraídas con extractor agéntico: {len(unique_transactions)}")
        
        return unique_transactions
    
    def _process_chunk_agentic(self, text: str, bank_name: str, chunk_num: int, total_chunks: int) -> List[Dict[str, Any]]:
        """
        Process a single chunk using agentic extraction.
        """
        prompt = self._create_agentic_prompt(text, bank_name, chunk_num, total_chunks)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using GPT-4o-mini for better reasoning
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert financial document analyzer. Your task is to extract transaction information from bank statements with high accuracy."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=4000,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            content = response.choices[0].message.content
            
            # Try to parse as JSON first
            try:
                result = json.loads(content)
                if isinstance(result, dict) and "transactions" in result:
                    return result["transactions"]
                elif isinstance(result, list):
                    return result
                else:
                    print(f"⚠️ Respuesta inesperada del extractor agéntico en chunk {chunk_num}")
                    return []
            except json.JSONDecodeError:
                # Fallback: try to extract from text response
                return self._parse_text_response(content)
                
        except Exception as e:
            print(f"❌ Error en extractor agéntico chunk {chunk_num}: {e}")
            return []
    
    def _create_agentic_prompt(self, text: str, bank_name: str, chunk_num: int, total_chunks: int) -> str:
        """
        Create an intelligent prompt for agentic extraction.
        """
        return f"""
You are analyzing a bank statement from {bank_name}. This is chunk {chunk_num} of {total_chunks}.

Your task is to extract ALL financial transactions from this text. A transaction typically contains:
- Date (when the transaction occurred)
- Description (what the transaction was for)
- Amount (positive for credits/deposits, negative for debits/withdrawals)

IMPORTANT GUIDELINES:
1. Look for patterns like: date + description + amount
2. Common date formats: DD-MMM-YYYY, DD/MM/YYYY, YYYY-MM-DD
3. Amounts usually appear with $, -, +, or currency symbols
4. Descriptions can be long and contain business names, locations, etc.
5. Some transactions might be payments (negative) or deposits (positive)
6. Be thorough - extract every transaction you can find

TEXT TO ANALYZE:
{text}

Please return ONLY a JSON array of transactions in this exact format:
[
  {{
    "fecha_operacion": "DD-MMM-YYYY",
    "descripcion": "Transaction description",
    "monto": 123.45,
    "categoria": "auto_categorized_category"
  }}
]

If no transactions are found, return an empty array: []

Focus on accuracy and completeness. Extract every transaction you can identify.
"""
    
    def _parse_text_response(self, text: str) -> List[Dict[str, Any]]:
        """
        Fallback parser for when JSON parsing fails.
        """
        transactions = []
        
        # Look for transaction patterns in the response
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to extract transaction info from line
            transaction = self._extract_from_line(line)
            if transaction:
                transactions.append(transaction)
                
        return transactions
    
    def _extract_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Extract transaction information from a single line.
        """
        # Common patterns for transaction lines
        patterns = [
            # Pattern: date - description - amount
            r'(\d{1,2}[-/]\w{3}[-/]\d{4})\s*[-–]\s*(.+?)\s*[-–]\s*\$?([+-]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            # Pattern: date description amount
            r'(\d{1,2}[-/]\w{3}[-/]\d{4})\s+(.+?)\s+\$?([+-]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            # Pattern: description amount date
            r'(.+?)\s+\$?([+-]?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s+(\d{1,2}[-/]\w{3}[-/]\d{4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 3:
                    date = groups[0] if groups[0].count('-') >= 2 or groups[0].count('/') >= 2 else groups[2]
                    description = groups[1] if len(groups) == 3 else groups[1]
                    amount_str = groups[2] if len(groups) == 3 else groups[1]
                    
                    try:
                        # Clean and parse amount
                        amount_str = amount_str.replace(',', '').replace('$', '').strip()
                        amount = float(amount_str)
                        
                        # Clean description
                        description = description.strip()
                        
                        return {
                            "fecha_operacion": date,
                            "descripcion": description,
                            "monto": amount,
                            "categoria": "auto_categorized"
                        }
                    except ValueError:
                        continue
                        
        return None
    
    def _split_text_into_chunks(self, text: str, max_tokens: int = 12000) -> List[str]:
        """
        Split text into chunks that fit within token limits.
        """
        # Rough estimation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        if len(text) <= max_chars:
            return [text]
            
        chunks = []
        current_chunk = ""
        
        lines = text.split('\n')
        for line in lines:
            if len(current_chunk) + len(line) + 1 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = line
                else:
                    # Line is too long, split it
                    chunks.append(line[:max_chars])
                    current_chunk = line[max_chars:]
            else:
                current_chunk += line + '\n'
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _deduplicate_transactions(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate transactions based on date, description, and amount.
        """
        seen = set()
        unique_transactions = []
        
        for transaction in transactions:
            # Create a unique key for each transaction
            key = (
                transaction.get('fecha_operacion', ''),
                transaction.get('descripcion', '')[:50],  # First 50 chars of description
                transaction.get('monto', 0)
            )
            
            if key not in seen:
                seen.add(key)
                unique_transactions.append(transaction)
                
        return unique_transactions 