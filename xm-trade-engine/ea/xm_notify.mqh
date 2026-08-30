#ifndef XM_NOTIFY_MQH
#define XM_NOTIFY_MQH

// GitHub Issue コメントと任意の Slack Incoming Webhook。秘密は input のみ。Git に書くな。

string XmJsonEscape(string s)
{
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   StringReplace(s, "\r", "");
   StringReplace(s, "\n", "\\n");
   return s;
}

string XmUtcDate()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return StringFormat("%04d-%02d-%02d", dt.year, dt.mon, dt.day);
}

int XmWebPost(const string url, string headers, const string body)
{
   char data[];
   char result[];
   string resultHeaders;
   int n = StringToCharArray(body, data, 0, WHOLE_ARRAY, CP_UTF8);
   if(n > 0)
      ArrayResize(data, n - 1);
   if(StringLen(headers) > 0 && StringFind(headers, "\r\n") < 0)
      headers = headers + "\r\n";
   if(StringFind(headers, "User-Agent:") < 0)
      headers += "User-Agent: xm-trade-engine\r\n";
   if(StringFind(headers, "Content-Type:") < 0)
      headers += "Content-Type: application/json\r\n";
   if(StringFind(url, "api.github.com") >= 0 && StringFind(headers, "Accept:") < 0)
      headers += "Accept: application/vnd.github+json\r\n";
   return WebRequest("POST", url, headers, 8000, data, result, resultHeaders);
}

void XmNotifyTrade(const bool enabled, const string authHeader, const string repo,
                   const string issueNumber, const string webhook,
                   const string marker, const string text)
{
   if(!enabled)
      return;
   Alert(text);
   Print(text);
   string body = marker + XmUtcDate() + "\n\n" + text;
   if(StringLen(webhook) > 0)
   {
      string payload = "{\"text\":\"" + XmJsonEscape(body) + "\"}";
      int code = XmWebPost(webhook, "", payload);
      if(code != 200 && code != 204)
         Print("notify webhook HTTP ", code);
   }
   if(StringLen(repo) > 0 && StringLen(issueNumber) > 0)
   {
      string url = "https://api.github.com/repos/" + repo + "/issues/" + issueNumber + "/comments";
      string payload = "{\"body\":\"" + XmJsonEscape(body) + "\"}";
      int code = XmWebPost(url, authHeader, payload);
      if(code != 201)
         Print("notify github HTTP ", code);
   }
}

bool XmDealNotify(const MqlTradeTransaction &trans, const long magic, const bool enabled,
                  const string authHeader, const string repo, const string issueNumber,
                  const string webhook, ulong &lastDeal)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD)
      return false;
   ulong deal = trans.deal;
   if(deal == 0 || deal == lastDeal)
      return false;
   if(!HistoryDealSelect(deal))
   {
      HistorySelect(TimeCurrent() - 7 * 86400, TimeCurrent() + 60);
      if(!HistoryDealSelect(deal))
         return false;
   }
   if(HistoryDealGetInteger(deal, DEAL_MAGIC) != magic)
      return false;
   string sym = HistoryDealGetString(deal, DEAL_SYMBOL);
   long entry = HistoryDealGetInteger(deal, DEAL_ENTRY);
   long dtype = HistoryDealGetInteger(deal, DEAL_TYPE);
   double vol = HistoryDealGetDouble(deal, DEAL_VOLUME);
   double price = HistoryDealGetDouble(deal, DEAL_PRICE);
   int digits = (int)SymbolInfoInteger(sym, SYMBOL_DIGITS);
   if(digits <= 0)
      digits = _Digits;
   string side = (dtype == DEAL_TYPE_BUY) ? "BUY" : "SELL";
   string text;
   string marker;
   if(entry == DEAL_ENTRY_IN)
   {
      marker = "xm-fill:";
      text = StringFormat("エントリー %s %s lot=%s @ %s",
                          sym, side, DoubleToString(vol, 2), DoubleToString(price, digits));
   }
   else if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_INOUT || entry == DEAL_ENTRY_OUT_BY)
   {
      marker = "xm-close:";
      double pnl = HistoryDealGetDouble(deal, DEAL_PROFIT)
                   + HistoryDealGetDouble(deal, DEAL_SWAP)
                   + HistoryDealGetDouble(deal, DEAL_COMMISSION);
      text = StringFormat("決済 %s deal=%s lot=%s @ %s pnl=%s",
                          sym, side, DoubleToString(vol, 2), DoubleToString(price, digits),
                          DoubleToString(pnl, 2));
   }
   else
      return false;
   lastDeal = deal;
   XmNotifyTrade(enabled, authHeader, repo, issueNumber, webhook, marker, text);
   return true;
}

#endif
