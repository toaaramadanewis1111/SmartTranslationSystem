{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 4,
   "metadata": {},
   "outputs": [
    {
     "ename": "ModuleNotFoundError",
     "evalue": "No module named 'llm'",
     "output_type": "error",
     "traceback": [
      "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[0;31mModuleNotFoundError\u001b[0m                       Traceback (most recent call last)",
      "\u001b[0;32m/tmp/ipykernel_12351/3101371187.py\u001b[0m in \u001b[0;36m<cell line: 0>\u001b[0;34m()\u001b[0m\n\u001b[0;32m----> 1\u001b[0;31m \u001b[0;32mfrom\u001b[0m \u001b[0mllm\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mschemas\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mipynb\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mTranslationResponse\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0m\u001b[1;32m      2\u001b[0m \u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      3\u001b[0m sample_response = {\n\u001b[1;32m      4\u001b[0m     \u001b[0;34m\"translation\"\u001b[0m\u001b[0;34m:\u001b[0m \u001b[0;34m\"كيف حالك؟\"\u001b[0m\u001b[0;34m,\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      5\u001b[0m     \u001b[0;34m\"source_language\"\u001b[0m\u001b[0;34m:\u001b[0m \u001b[0;34m\"en\"\u001b[0m\u001b[0;34m,\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n",
      "\u001b[0;31mModuleNotFoundError\u001b[0m: No module named 'llm'",
      "",
      "\u001b[0;31m---------------------------------------------------------------------------\u001b[0;32m\nNOTE: If your import is failing due to a missing package, you can\nmanually install dependencies using either !pip or !apt.\n\nTo view examples of installing some common dependencies, click the\n\"Open Examples\" button below.\n\u001b[0;31m---------------------------------------------------------------------------\u001b[0m\n"
     ]
    }
   ],
   "source": [
    "\n",
    "from llm.schemas.ipynb import TranslationResponse\n",
    "\n",
    "sample_response = {\n",
    "    \"translation\": \"كيف حالك؟\",\n",
    "    \"source_language\": \"en\",\n",
    "    \"target_language\": \"ar\",\n",
    "    \"style\": \"natural\",\n",
    "    \"ambiguity\": {\n",
    "        \"is_ambiguous\": False,\n",
    "        \"chosen_meaning\": None,\n",
    "        \"confidence\": \"high\"\n",
    "    },\n",
    "    \"alternatives\": [\n",
    "        \"كيف أمورك؟\",\n",
    "        \"عامل إيه؟\"\n",
    "    ]\n",
    "}\n",
    "\n",
    "result = TranslationResponse(**sample_response)\n",
    "\n",
    "print(result.model_dump_json(indent=4))\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.13.18"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
