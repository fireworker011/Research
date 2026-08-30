// XM + Cursor/Grok 自動売買の実時間側。
// Node の GitHub cron は遅延するので、発注の正は本 EA（ローカル H1 戦略）。
// commander.json の HALT だけクラウドから読む。口座番号・パスワードは書くな。

#property copyright "xm-trade-engine"
#property version   "1.11"
#property description "XM MT5 majors. Local H1 EMA. Fill/close notify to GitHub Issue."

#include <Trade/Trade.mqh>
#include "xm_notify.mqh"

input group "Commander"
input string CommanderURL = ""; // GitHub raw commander.json。空ならローカルリスクのみ
input string CommanderAuthHeader = ""; // 非公開repoなら "Authorization: token ghp_..." 。Gitに書くな
input bool   FailClosedOnFetchError = true;
input int    CommanderPollSeconds = 60;

input group "Notify (fill / close)"
input bool   NotifyEnabled = true;
input string GitHubRepo = "fireworker011/Research";
input string NotifyIssueNumber = "";
input string SlackWebhookURL = "";

input group "Risk"
input int    MagicNumber = 260830;
input string SymbolSuffix = "";
input double RiskPercent = 0.5;
input double MaxLot = 0.10;
input double MinLot = 0.01;
input int    MaxPositions = 2;
input int    MaxDailyLossPct = 2;

input group "Strategy (must match config/strategy.json)"
input int    EmaFast = 20;
input int    EmaSlow = 50;
input int    RsiPeriod = 14;
input int    AtrPeriod = 14;
input double SlAtr = 1.5;
input double TpAtr = 2.0;
input int    RsiOverbought = 70;
input int    RsiOversold = 30;
input int    SessionStartUtc = 7;
input int    SessionEndUtc = 21;
input int    FridayFlattenUtc = 18;

CTrade trade;
int hFast = INVALID_HANDLE;
int hSlow = INVALID_HANDLE;
int hRsi = INVALID_HANDLE;
int hAtr = INVALID_HANDLE;
string gCommand = "PAPER_ONLY";
datetime gLastFetch = 0;
double gDayStartEquity = 0;
int gDayStamp = 0;
string gIssueNumber = "";
ulong gLastNotifiedDeal = 0;
int gFetchFails = 0;
bool gFetchBlocked = false;

int OnInit()
{
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(20);
   hFast = iMA(_Symbol, PERIOD_H1, EmaFast, 0, MODE_EMA, PRICE_CLOSE);
   hSlow = iMA(_Symbol, PERIOD_H1, EmaSlow, 0, MODE_EMA, PRICE_CLOSE);
   hRsi = iRSI(_Symbol, PERIOD_H1, RsiPeriod, PRICE_CLOSE);
   hAtr = iATR(_Symbol, PERIOD_H1, AtrPeriod);
   if(hFast == INVALID_HANDLE || hSlow == INVALID_HANDLE || hRsi == INVALID_HANDLE || hAtr == INVALID_HANDLE)
      return INIT_FAILED;
   gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   gDayStamp = DayStamp();
   EventSetTimer(1);
   if(StringLen(SymbolSuffix) > 0 && StringFind(_Symbol, SymbolSuffix) < 0)
      Print("warning: attach this EA to the XM symbol that already has suffix ", SymbolSuffix);
   Print("XMGrokEngine init. commander=", CommanderURL);
   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   if(hFast != INVALID_HANDLE) IndicatorRelease(hFast);
   if(hSlow != INVALID_HANDLE) IndicatorRelease(hSlow);
   if(hRsi != INVALID_HANDLE) IndicatorRelease(hRsi);
   if(hAtr != INVALID_HANDLE) IndicatorRelease(hAtr);
}

void OnTimer()
{
   PollCommander();
}

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request, const MqlTradeResult &result)
{
   string issue = StringLen(NotifyIssueNumber) > 0 ? NotifyIssueNumber : gIssueNumber;
   XmDealNotify(trans, MagicNumber, NotifyEnabled, CommanderAuthHeader, GitHubRepo, issue, SlackWebhookURL, gLastNotifiedDeal);
}

void OnTick()
{
   if(DayStamp() != gDayStamp)
   {
      gDayStamp = DayStamp();
      gDayStartEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   }

   PollCommander();

   if(DailyLossHit())
   {
      CloseThisSymbol("daily_loss");
      return;
   }

   if(gCommand == "HALT")
   {
      CloseThisSymbol("halt");
      return;
   }

   if(!IsNewH1Bar())
      return;

   if(FridayFlatten())
   {
      CloseThisSymbol("friday_flatten");
      return;
   }

   if(!InSession())
      return;

   double emaFast, emaSlow, emaFastPrev, rsi, atr, close1, close2;
   if(!Copy1(hFast, 1, emaFast) || !Copy1(hSlow, 1, emaSlow) || !Copy1(hFast, 2, emaFastPrev))
      return;
   if(!Copy1(hRsi, 1, rsi) || !Copy1(hAtr, 1, atr))
      return;
   close1 = iClose(_Symbol, PERIOD_H1, 1);
   close2 = iClose(_Symbol, PERIOD_H1, 2);
   if(close1 <= 0 || atr <= 0)
      return;

   int pos = CountMagicPositions();
   int side = PositionSide();

   if(side > 0 && emaFast < emaSlow)
   {
      CloseThisSymbol("trend_flip");
      return;
   }
   if(side < 0 && emaFast > emaSlow)
   {
      CloseThisSymbol("trend_flip");
      return;
   }
   if(side != 0)
      return;

   if(pos >= MaxPositions)
      return;
   if(!AllowNewEntries())
      return;

   double riskMul = (gCommand == "REDUCE_RISK") ? 0.5 : 1.0;
   bool bull = emaFast > emaSlow;
   bool bear = emaFast < emaSlow;
   bool crossUp = close2 <= emaFastPrev && close1 > emaFast;
   bool crossDown = close2 >= emaFastPrev && close1 < emaFast;

   if(bull && crossUp && rsi < RsiOverbought)
      OpenDir(ORDER_TYPE_BUY, close1, atr, riskMul);
   else if(bear && crossDown && rsi > RsiOversold)
      OpenDir(ORDER_TYPE_SELL, close1, atr, riskMul);
}

void OpenDir(ENUM_ORDER_TYPE type, double close1, double atr, double riskMul)
{
   double slDist = atr * SlAtr;
   double tpDist = atr * TpAtr;
   double sl, tp;
   if(type == ORDER_TYPE_BUY)
   {
      sl = close1 - slDist;
      tp = close1 + tpDist;
   }
   else
   {
      sl = close1 + slDist;
      tp = close1 - tpDist;
   }
   double lot = LotFromRisk(close1, sl, riskMul);
   if(lot < MinLot)
      return;
   string comment = "xmge";
   if(type == ORDER_TYPE_BUY)
      trade.Buy(lot, _Symbol, 0, sl, tp, comment);
   else
      trade.Sell(lot, _Symbol, 0, sl, tp, comment);
}

double LotFromRisk(double price, double sl, double riskMul)
{
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskPct = RiskPercent * riskMul;
   double slDist = MathAbs(price - sl);
   if(slDist <= 0 || equity <= 0)
      return 0;
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tickSize <= 0 || tickValue <= 0)
      return 0;
   double lossPerLot = (slDist / tickSize) * tickValue;
   if(lossPerLot <= 0)
      return 0;
   double lot = (equity * (riskPct / 100.0)) / lossPerLot;
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0) step = 0.01;
   lot = MathFloor(lot / step) * step;
   if(lot > MaxLot) lot = MaxLot;
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(vmax > 0 && lot > vmax) lot = vmax;
   return lot;
}

bool Copy1(int handle, int shift, double &out)
{
   double buf[];
   if(CopyBuffer(handle, 0, shift, 1, buf) < 1)
      return false;
   out = buf[0];
   return MathIsValidNumber(out);
}

bool IsNewH1Bar()
{
   static datetime last = 0;
   datetime t = iTime(_Symbol, PERIOD_H1, 0);
   if(t == 0 || t == last)
      return false;
   last = t;
   return true;
}

int DayStamp()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return dt.year * 10000 + dt.mon * 100 + dt.day;
}

bool InSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   if(dt.day_of_week == 0 || dt.day_of_week == 6)
      return false;
   return dt.hour >= SessionStartUtc && dt.hour < SessionEndUtc;
}

bool FridayFlatten()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return dt.day_of_week == 5 && dt.hour >= FridayFlattenUtc;
}

bool AllowNewEntries()
{
   if(gCommand == "HALT")
      return false;
   if(gFetchBlocked)
      return false;
   long mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(mode == ACCOUNT_TRADE_MODE_REAL)
      return gCommand == "RESUME";
   return true;
}

bool DailyLossHit()
{
   if(gDayStartEquity <= 0)
      return false;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   double lossPct = ((gDayStartEquity - eq) / gDayStartEquity) * 100.0;
   return lossPct >= MaxDailyLossPct;
}

int CountMagicPositions()
{
   int n = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      n++;
   }
   return n;
}

int PositionSide()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      long type = PositionGetInteger(POSITION_TYPE);
      if(type == POSITION_TYPE_BUY) return 1;
      if(type == POSITION_TYPE_SELL) return -1;
   }
   return 0;
}

void CloseThisSymbol(string reason)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket == 0) continue;
      if(PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol) continue;
      trade.PositionClose(ticket);
      Print("close ", reason, " ticket=", ticket);
   }
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
      // 一瞬の通信断で建玉を閉じない。5回連続で新規だけ止める。
      gFetchFails++;
      if(FailClosedOnFetchError && gFetchFails >= 5 && !gFetchBlocked)
      {
         gFetchBlocked = true;
         Print("commander unreachable x", gFetchFails, ": new entries blocked");
      }
      return;
   }
   gFetchFails = 0;
   gFetchBlocked = false;
   string cmd = ExtractJsonString(json, "command");
   StringToUpper(cmd);
   if(cmd == "HALT" || cmd == "PAPER_ONLY" || cmd == "RESUME" || cmd == "REDUCE_RISK")
      gCommand = cmd;
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
   headers += "User-Agent: XMGrokEngine\r\n";
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
