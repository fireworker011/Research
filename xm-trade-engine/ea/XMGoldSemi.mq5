// Gold 完全自動。ブローカー 0-7 / 7-11。IDLE で OCO 両方。SKIP/HALT のみ人間。告知は xm-fill / xm-close。

#property copyright "xm-trade-engine"
#property version   "1.20"
#property description "XM GOLD full-auto. Broker-time OCO, GitHub fill/close notify."

#include <Trade/Trade.mqh>
#include "xm_notify.mqh"

input group "Commander"
input string CommanderURL = "";
input string CommanderAuthHeader = "";
input bool   FailClosedOnFetchError = true;
input int    CommanderPollSeconds = 30;

input group "Notify (fill / close)"
input bool   NotifyEnabled = true;
input string GitHubRepo = "fireworker011/Research";
input string NotifyIssueNumber = "";
input string SlackWebhookURL = "";

input group "Risk"
input int    MagicNumber = 260831;
input double RiskPercent = 0.5;
input double MaxLot = 0.10;
input double MinLot = 0.01;
input int    MaxDailyLossPct = 2;
input double MaxSpreadPrice = 0.80;

input group "Gold London (broker server time, same as GoldLondonBreakout)"
input int    AsiaStartHour = 0;
input int    AsiaEndHour = 7;
input int    LondonStartHour = 7;
input int    LondonEndHour = 11;
input int    DailyAtrPeriod = 14;
input int    AtrPeriod = 14;
input double MinRangeAtrFrac = 0.15;
input double MaxRangeAtrFrac = 0.70;
input double BreakoutBufferAtr = 0.15;
input double SlAtr = 1.2;
input double RewardMultiple = 1.8;
input bool   SkipFirstFriday = true;
input bool   AutoOco = true;

CTrade trade;
int hAtr = INVALID_HANDLE;
int hDailyAtr = INVALID_HANDLE;
string gCommand = "PAPER_ONLY";
string gGoldArm = "IDLE";
string gGoldArmDate = "";
datetime gLastFetch = 0;
double gDayStartEquity = 0;
int gDayStamp = 0;
double gAsiaHigh = 0;
double gAsiaLow = 0;
double gAsiaClose = 0;
bool gAsiaLocked = false;
bool gPlacedToday = false;
bool gAlerted = false;
string gIssueNumber = "";
ulong gLastNotifiedDeal = 0;

int OnInit()
{
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(50);
   hAtr = iATR(_Symbol, PERIOD_M15, AtrPeriod);
   hDailyAtr = iATR(_Symbol, PERIOD_D1, DailyAtrPeriod);
   if(hAtr == INVALID_HANDLE || hDailyAtr == INVALID_HANDLE)
      return INIT_FAILED;
   gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   gDayStamp = BrokerDayStamp();
   EventSetTimer(1);
   if(StringFind(_Symbol, "GOLD") < 0 && StringFind(_Symbol, "XAU") < 0)
      Print("warning: attach to GOLD/XAUUSD M15, chart is ", _Symbol);
   if(AccountInfoInteger(ACCOUNT_MARGIN_MODE) == ACCOUNT_MARGIN_MODE_RETAIL_NETTING)
      Print("warning: netting account. Keep this EA alone on the symbol.");
   Print("XMGoldSemi init broker-time asia ", AsiaStartHour, "-", AsiaEndHour,
         " london ", LondonStartHour, "-", LondonEndHour);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   ObjectDelete(0, "xmge_asia_high");
   ObjectDelete(0, "xmge_asia_low");
   Comment("");
   if(hAtr != INVALID_HANDLE) IndicatorRelease(hAtr);
   if(hDailyAtr != INVALID_HANDLE) IndicatorRelease(hDailyAtr);
}

void OnTimer()
{
   Run();
}

void OnTick()
{
   Run();
}

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request, const MqlTradeResult &result)
{
   string issue = StringLen(NotifyIssueNumber) > 0 ? NotifyIssueNumber : gIssueNumber;
   XmDealNotify(trans, MagicNumber, NotifyEnabled, CommanderAuthHeader, GitHubRepo, issue, SlackWebhookURL, gLastNotifiedDeal);
}

void Run()
{
   if(BrokerDayStamp() != gDayStamp)
   {
      gDayStamp = BrokerDayStamp();
      gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      gAsiaLocked = false;
      gPlacedToday = false;
      gAlerted = false;
      gAsiaHigh = 0;
      gAsiaLow = 0;
      gAsiaClose = 0;
   }

   PollCommander();
   PaintStatus();

   if(DailyLossHit() || gCommand == "HALT")
   {
      CancelPendings();
      CloseMagic("halt");
      return;
   }

   MqlDateTime sv;
   TimeToStruct(TimeCurrent(), sv);
   if(sv.day_of_week == 0 || sv.day_of_week == 6)
      return;
   if(SkipFirstFriday && sv.day_of_week == 5 && sv.day <= 7)
      return;

   if(!gAsiaLocked && sv.hour >= AsiaEndHour)
      LockAsiaRange();

   ManageOcoFill();
   if(CountMagicPositions() > 0)
      gPlacedToday = true;

   if(gGoldArm == "SKIP" && gGoldArmDate == UtcDateStr())
   {
      CancelPendings();
      if(CountMagicPositions() == 0)
         gPlacedToday = true;
      return;
   }

   if(!gAsiaLocked || gPlacedToday)
      return;
   if(sv.hour < LondonStartHour || sv.hour >= LondonEndHour)
   {
      if(sv.hour >= LondonEndHour)
         CancelPendings();
      return;
   }
   if(gGoldArm != "ARM" && gGoldArm != "BUY" && gGoldArm != "SELL" && gGoldArm != "IDLE")
      return;
   if(gGoldArm == "BUY" || gGoldArm == "SELL")
   {
      if(gGoldArmDate != UtcDateStr())
         return;
   }
   else if(gGoldArm == "ARM" && StringLen(gGoldArmDate) > 0 && gGoldArmDate != UtcDateStr())
      return;
   else if(gGoldArm == "IDLE" && !AutoOco)
      return;
   if(!AllowRealOrDemo())
      return;

   double spread = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(spread > MaxSpreadPrice)
      return;

   PlaceStops((gGoldArm == "BUY" || gGoldArm == "SELL") ? gGoldArm : "ARM");
}

void LockAsiaRange()
{
   datetime start = BrokerHourToday(AsiaStartHour);
   datetime end = BrokerHourToday(AsiaEndHour);
   gAsiaHigh = 0;
   gAsiaLow = 0;
   int bars = iBars(_Symbol, PERIOD_M15);
   bool any = false;
   for(int i = 1; i < bars && i < 120; i++)
   {
      datetime t = iTime(_Symbol, PERIOD_M15, i);
      if(t == 0) continue;
      if(t < start) break;
      if(t >= end) continue;
      double h = iHigh(_Symbol, PERIOD_M15, i);
      double l = iLow(_Symbol, PERIOD_M15, i);
      if(!any)
      {
         gAsiaHigh = h;
         gAsiaLow = l;
         gAsiaClose = iClose(_Symbol, PERIOD_M15, i);
         any = true;
      }
      else
      {
         if(h > gAsiaHigh) gAsiaHigh = h;
         if(l < gAsiaLow) gAsiaLow = l;
      }
   }
   if(!any || gAsiaHigh <= gAsiaLow)
      return;
   double dailyAtr, atr;
   if(!Copy1(hDailyAtr, 1, dailyAtr) || !Copy1(hAtr, 1, atr) || dailyAtr <= 0 || atr <= 0)
      return;
   double range = gAsiaHigh - gAsiaLow;
   double frac = range / dailyAtr;
   if(frac < MinRangeAtrFrac || frac > MaxRangeAtrFrac)
   {
      Print("asia skip frac=", frac);
      return;
   }
   gAsiaLocked = true;
   DrawLevels();
   if(!gAlerted)
   {
      Alert("XMGoldSemi asia locked. Wait for ENTRY/ARM. high=", gAsiaHigh, " low=", gAsiaLow);
      gAlerted = true;
   }
   Print("asia locked high=", gAsiaHigh, " low=", gAsiaLow, " frac=", frac);
}

void PlaceStops(string side)
{
   if(CountMagicPositions() > 0)
   {
      gPlacedToday = true;
      return;
   }
   double atr;
   if(!Copy1(hAtr, 1, atr) || atr <= 0)
      return;
   double buffer = atr * BreakoutBufferAtr;
   double slDist = atr * SlAtr;
   double tpDist = slDist * RewardMultiple;
   double buy = NormalizeDouble(gAsiaHigh + buffer, _Digits);
   double sell = NormalizeDouble(gAsiaLow - buffer, _Digits);
   datetime expiry = BrokerHourToday(LondonEndHour);
   if(expiry <= TimeCurrent())
      return;
   bool wantBuy = (side == "ARM" || side == "BUY");
   bool wantSell = (side == "ARM" || side == "SELL");
   double riskPct = RiskPercent;
   if(gCommand == "REDUCE_RISK")
      riskPct = RiskPercent * 0.5;
   if(wantBuy && !HasPendingType(ORDER_TYPE_BUY_STOP) && StopsClear(buy))
   {
      double lotBuy = LotFromRisk(buy, buy - slDist, riskPct);
      if(lotBuy >= MinLot)
         trade.BuyStop(lotBuy, buy, _Symbol, NormalizeDouble(buy - slDist, _Digits),
                       NormalizeDouble(buy + tpDist, _Digits), ORDER_TIME_SPECIFIED, expiry, "xmge-gold");
   }
   else if(wantBuy && !HasPendingType(ORDER_TYPE_BUY_STOP))
      Print("buy stop too close to market");
   if(wantSell && !HasPendingType(ORDER_TYPE_SELL_STOP) && StopsClear(sell))
   {
      double lotSell = LotFromRisk(sell, sell + slDist, riskPct);
      if(lotSell >= MinLot)
         trade.SellStop(lotSell, sell, _Symbol, NormalizeDouble(sell + slDist, _Digits),
                        NormalizeDouble(sell - tpDist, _Digits), ORDER_TIME_SPECIFIED, expiry, "xmge-gold");
   }
   else if(wantSell && !HasPendingType(ORDER_TYPE_SELL_STOP))
      Print("sell stop too close to market");
   bool buyOk = !wantBuy || HasPendingType(ORDER_TYPE_BUY_STOP);
   bool sellOk = !wantSell || HasPendingType(ORDER_TYPE_SELL_STOP);
   if((wantBuy || wantSell) && buyOk && sellOk)
      gPlacedToday = true;
}

bool HasPendingType(ENUM_ORDER_TYPE typ)
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      if((ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE) == typ) return true;
   }
   return false;
}

bool StopsClear(double pending)
{
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   int stops = (int)SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist = stops * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
   if(minDist <= 0) minDist = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * 50;
   if(MathAbs(pending - ask) < minDist) return false;
   if(MathAbs(pending - bid) < minDist) return false;
   return true;
}

void ManageOcoFill()
{
   if(CountMagicPositions() > 0)
      CancelPendings();
}

int CountMagicPendings()
{
   int n = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      n++;
   }
   return n;
}

int CountMagicPositions()
{
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      n++;
   }
   return n;
}

void CancelPendings()
{
   for(int i = OrdersTotal() - 1; i >= 0; i--)
   {
      ulong ticket = OrderGetTicket(i);
      if(ticket == 0) continue;
      if(OrderGetInteger(ORDER_MAGIC) != MagicNumber) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol) continue;
      trade.OrderDelete(ticket);
   }
}

void CloseMagic(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      trade.PositionClose(ticket);
      Print("close ", reason);
   }
}

double LotFromRisk(double price, double sl, double riskPct)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double slDist = MathAbs(price - sl);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(slDist <= 0 || equity <= 0 || tickSize <= 0 || tickValue <= 0)
      return 0;
   double lossPerLot = (slDist / tickSize) * tickValue;
   if(lossPerLot <= 0) return 0;
   double lot = (equity * (riskPct / 100.0)) / lossPerLot;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0) step = 0.01;
   lot = MathFloor(lot / step) * step;
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   if(vmin > 0 && lot < vmin) return 0;
   if(lot > MaxLot) lot = MaxLot;
   return lot;
}

bool AllowRealOrDemo()
{
   long mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(mode == ACCOUNT_TRADE_MODE_REAL)
      return gCommand == "RESUME";
   return true;
}

bool DailyLossHit()
{
   if(gDayStartEquity <= 0) return false;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   return ((gDayStartEquity - eq) / gDayStartEquity) * 100.0 >= MaxDailyLossPct;
}

bool Copy1(int handle, int shift, double &out)
{
   double buf[];
   if(CopyBuffer(handle, 0, shift, 1, buf) < 1) return false;
   out = buf[0];
   return MathIsValidNumber(out);
}

int BrokerDayStamp()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   return dt.year * 10000 + dt.mon * 100 + dt.day;
}

datetime BrokerHourToday(int hour)
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   dt.hour = hour;
   dt.min = 0;
   dt.sec = 0;
   return StructToTime(dt);
}

string UtcDateStr()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return StringFormat("%04d-%02d-%02d", dt.year, dt.mon, dt.day);
}

void DrawLevels()
{
   if(gAsiaHigh <= 0) return;
   if(ObjectFind(0, "xmge_asia_high") < 0)
      ObjectCreate(0, "xmge_asia_high", OBJ_HLINE, 0, 0, gAsiaHigh);
   ObjectSetDouble(0, "xmge_asia_high", OBJPROP_PRICE, gAsiaHigh);
   ObjectSetInteger(0, "xmge_asia_high", OBJPROP_COLOR, clrDodgerBlue);
   if(ObjectFind(0, "xmge_asia_low") < 0)
      ObjectCreate(0, "xmge_asia_low", OBJ_HLINE, 0, 0, gAsiaLow);
   ObjectSetDouble(0, "xmge_asia_low", OBJPROP_PRICE, gAsiaLow);
   ObjectSetInteger(0, "xmge_asia_low", OBJPROP_COLOR, clrTomato);
}

string ChartSuggestedSide()
{
   if(gAsiaHigh <= gAsiaLow) return "NONE";
   double pos = (gAsiaClose - gAsiaLow) / (gAsiaHigh - gAsiaLow);
   if(pos >= 2.0 / 3.0) return "BUY";
   if(pos <= 1.0 / 3.0) return "SELL";
   return "NONE";
}

void PaintStatus()
{
   Comment(
      "XMGoldSemi GOLD M15 broker-time 0-7 / 7-11\n",
      "cmd=", gCommand, " gold_arm=", gGoldArm, " date=", gGoldArmDate, "\n",
      "asia_locked=", (gAsiaLocked ? "yes" : "no"),
      " high=", DoubleToString(gAsiaHigh, _Digits),
      " low=", DoubleToString(gAsiaLow, _Digits),
      " close=", DoubleToString(gAsiaClose, _Digits),
      " chart_side=", ChartSuggestedSide(),
      " auto=", (AutoOco ? "yes" : "no"), "\n",
      "notify_issue=", (StringLen(NotifyIssueNumber) > 0 ? NotifyIssueNumber : gIssueNumber), "\n",
      "placed=", (gPlacedToday ? "yes" : "no"),
      " pendings=", CountMagicPendings(),
      " positions=", CountMagicPositions()
   );
}

void PollCommander()
{
   if(StringLen(CommanderURL) == 0)
      return;
   datetime now = TimeGMT();
   if(gLastFetch != 0 && now - gLastFetch < CommanderPollSeconds)
      return;
   gLastFetch = now;
   string json = FetchJson();
   if(json == "")
   {
      if(FailClosedOnFetchError)
      {
         gCommand = "HALT";
         gGoldArm = "IDLE";
      }
      return;
   }
   string cmd = ExtractJsonString(json, "command");
   StringToUpper(cmd);
   if(cmd == "HALT" || cmd == "PAPER_ONLY" || cmd == "RESUME" || cmd == "REDUCE_RISK")
      gCommand = cmd;
   string arm = ExtractJsonString(json, "gold_arm");
   StringToUpper(arm);
   if(arm == "ARM" || arm == "SKIP" || arm == "IDLE" || arm == "BUY" || arm == "SELL")
      gGoldArm = arm;
   gGoldArmDate = ExtractJsonString(json, "gold_arm_date");
   string issue = ExtractJsonString(json, "issue_number");
   if(StringLen(issue) > 0)
      gIssueNumber = issue;
}

string FetchJson()
{
   char post[];
   char result[];
   string resultHeaders;
   string headers = CommanderAuthHeader;
   if(StringLen(headers) > 0 && StringFind(headers, "\r\n") < 0)
      headers = headers + "\r\n";
   headers += "User-Agent: XMGoldSemi\r\n";
   if(StringFind(CommanderURL, "api.github.com") >= 0)
      headers += "Accept: application/vnd.github.raw\r\n";
   int code = WebRequest("GET", CommanderURL, headers, 8000, post, result, resultHeaders);
   if(code != 200)
   {
      Print("commander HTTP ", code);
      return "";
   }
   return CharArrayToString(result, 0, WHOLE_ARRAY, CP_UTF8);
}

string ExtractJsonString(string json, string key)
{
   string needle = "\"" + key + "\"";
   int p = StringFind(json, needle);
   if(p < 0) return "";
   int colon = StringFind(json, ":", p);
   if(colon < 0) return "";
   int q1 = StringFind(json, "\"", colon);
   if(q1 < 0) return "";
   int q2 = StringFind(json, "\"", q1 + 1);
   if(q2 < 0) return "";
   return StringSubstr(json, q1 + 1, q2 - q1 - 1);
}
